import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session

from app.config import get_db
from app.servicios.manager_aprendizaje_ia import ManagerAprendizajeIA

router = APIRouter(prefix="/ia", tags=["IA Lectura"])

manager_ia = ManagerAprendizajeIA()

UPLOAD_DIR = "uploads/audio"


def _asegurar_directorio() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analizar-lectura")
async def analizar_lectura_endpoint(
    estudiante_id: int = Form(...),
    contenido_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Sube un audio de lectura, ejecuta el análisis de IA (Whisper) y devuelve:
    - precisión
    - errores
    - feedback
    - ejercicios recomendados
    """
    _asegurar_directorio()

    ext = os.path.splitext(audio.filename or "")[1] or ".wav"
    filename = f"{uuid.uuid4().hex}{ext}"
    audio_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

        resultado = await manager_ia.procesar_lectura(
            db=db,
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            audio_path=audio_path,
        )

        return resultado

    except Exception as e:
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))
