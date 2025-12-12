# app/routers/ia_routes.py

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_db
from app.logs.logger import logger
from app.modelos import (
    ContenidoLectura,
    Estudiante,
    Padre,
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario
from app.servicios.ia_lectura_service import ServicioAnalisisLectura
from app.servicios.manager_aprendizaje_ia import ManagerAprendizajeIA

router = APIRouter(prefix="/ia", tags=["IA Lectura"])

# Directorios para guardar audios
UPLOAD_AUDIO_DIR = "uploads/audio"
TTS_DIR = "uploads/tts"
PRACTICA_AUDIO_DIR = "uploads/practica"

analizador = ServicioAnalisisLectura(modelo="small")
manager_ia = ManagerAprendizajeIA()


def _asegurar_directorios() -> None:
    os.makedirs(UPLOAD_AUDIO_DIR, exist_ok=True)
    os.makedirs(TTS_DIR, exist_ok=True)
    os.makedirs(PRACTICA_AUDIO_DIR, exist_ok=True)


def _obtener_padre_actual(db: Session, usuario_actual: Usuario) -> Padre:
    padre = (
        db.query(Padre)
        .filter(Padre.usuario_id == usuario_actual.id)
        .first()
    )
    if not padre:
        raise HTTPException(
            status_code=403,
            detail="El usuario actual no es un padre registrado.",
        )
    return padre


def _verificar_estudiante_de_padre(
    db: Session,
    padre: Padre,
    estudiante_id: int,
) -> Estudiante:
    """
    Verifica que el estudiante pertenezca a este padre.
    Asume relación Estudiante.padre_id -> Padre.id
    (ajusta aquí si usas acceso_padre u otra tabla intermedia).
    """
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.padre_id == padre.id,
        )
        .first()
    )
    if not estudiante:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a este estudiante.",
        )
    return estudiante


# ============================================================
# 1. Obtener texto de la lectura (para mostrar en pantalla)
# ============================================================
@router.get("/lectura-texto/{contenido_id}")
def obtener_texto_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Devuelve el título y el contenido de la lectura.
    """
    contenido = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == contenido_id)
        .first()
    )
    if not contenido:
        raise HTTPException(status_code=404, detail="Contenido de lectura no encontrado.")

    return {
        "id": contenido.id,
        "titulo": contenido.titulo,
        "contenido": contenido.contenido,
    }


# ============================================================
# 2. Obtener audio de la lectura (TTS o audio grabado)
#    Por ahora asumimos que todavía no tienes TTS en backend
#    así que opcionalmente podrías servir un MP3 si existe.
# ============================================================
@router.get("/lectura-audio/{contenido_id}")
def obtener_audio_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    En este ejemplo, si tuvieras un audio guardado en disco
    podrías devolverlo aquí. Por ahora asumimos que no, y el
    frontend usa TTS del navegador o solo muestra el texto.
    """
    contenido = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == contenido_id)
        .first()
    )
    if not contenido:
        raise HTTPException(status_code=404, detail="Contenido de lectura no encontrado.")

    if contenido.audio_url and os.path.exists(contenido.audio_url):
        return FileResponse(contenido.audio_url, media_type="audio/mpeg")

    # Si no hay audio físico, devolvemos 404 y el front puede usar TTS del navegador
    raise HTTPException(status_code=404, detail="No hay audio disponible para esta lectura.")


# ============================================================
# 3. Analizar lectura completa (padre logueado, hijo seleccionado)
# ============================================================
@router.post("/analizar-lectura")
async def analizar_lectura_endpoint(
    estudiante_id: int = Form(...),
    contenido_id: int = Form(...),
    audio: UploadFile = File(...),
    evaluacion_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    El padre está logueado, pero enviamos estudiante_id desde el front
    (niño seleccionado en el panel del padre). Aquí verificamos que ese
    estudiante realmente pertenezca a este padre.
    """
    _asegurar_directorios()

    padre = _obtener_padre_actual(db, usuario_actual)
    _verificar_estudiante_de_padre(db, padre, estudiante_id)

    ext = os.path.splitext(audio.filename or "")[1] or ".wav"
    filename = f"lectura_{estudiante_id}_{contenido_id}_{uuid.uuid4().hex}{ext}"
    audio_path = os.path.join(UPLOAD_AUDIO_DIR, filename)

    try:
        with open(audio_path, "wb") as f:
            contenido_bytes = await audio.read()
            f.write(contenido_bytes)

        resultado = analizador.analizar_lectura(
            db=db,
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            audio_path=audio_path,
            evaluacion_id=evaluacion_id,
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error al analizar lectura con IA")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 4. Práctica de ejercicio (IA didáctica)
# ============================================================
@router.post("/practicar-ejercicio")
async def practicar_ejercicio_endpoint(
    estudiante_id: int = Form(...),
    ejercicio_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    El padre selecciona un ejercicio para el hijo.
    Verificamos que el estudiante pertenezca al padre.
    """
    _asegurar_directorios()

    padre = _obtener_padre_actual(db, usuario_actual)
    _verificar_estudiante_de_padre(db, padre, estudiante_id)

    ext = os.path.splitext(audio.filename or "")[1] or ".wav"
    filename = f"practica_{ejercicio_id}_{uuid.uuid4().hex}{ext}"
    audio_path = os.path.join(PRACTICA_AUDIO_DIR, filename)

    try:
        with open(audio_path, "wb") as f:
            contenido_bytes = await audio.read()
            f.write(contenido_bytes)

        resultado = manager_ia.practicar_ejercicio(
            db=db,
            estudiante_id=estudiante_id,
            ejercicio_id=ejercicio_id,
            audio_path=audio_path,
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error al analizar práctica de ejercicio con IA")
        raise HTTPException(status_code=500, detail=str(e))
    
    # app/routers/ia_routes.py
@router.get("/lectura-texto/{contenido_id}")
def obtener_texto_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    contenido = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == contenido_id)
        .first()
    )
    if not contenido:
        raise HTTPException(status_code=404, detail="Contenido de lectura no encontrado.")

    return {
        "id": contenido.id,
        "titulo": contenido.titulo,
        "contenido": contenido.contenido,
    }

