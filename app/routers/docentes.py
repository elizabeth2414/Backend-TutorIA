from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List

from app.config import get_db
from app.esquemas.docente import DocenteCreate, DocenteResponse, DocenteUpdate
from app.servicios.docente import (
    crear_docente, obtener_docentes, obtener_docente,
    actualizar_docente, eliminar_docente
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Docente, Estudiante, Actividad

router = APIRouter(prefix="/docentes", tags=["docentes"])


# ================================================================
#                     CRUD DOCENTE (YA EXISTÍA)
# ================================================================

@router.post("/", response_model=DocenteResponse)
def crear_nuevo_docente(
    docente: DocenteCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nuevo docente"""
    return crear_docente(db, docente)


@router.get("/", response_model=List[DocenteResponse])
def listar_docentes(
    skip: int = 0,
    limit: int = 100,
    activo: bool = True,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar todos los docentes"""
    return obtener_docentes(db, skip=skip, limit=limit, activo=activo)


@router.get("/{docente_id}", response_model=DocenteResponse)
def obtener_docente_por_id(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener docente por ID"""
    db_docente = obtener_docente(db, docente_id)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return db_docente


@router.put("/{docente_id}", response_model=DocenteResponse)
def actualizar_docente_endpoint(
    docente_id: int,
    docente: DocenteUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar docente"""
    return actualizar_docente(db, docente_id, docente)


@router.delete("/{docente_id}")
def eliminar_docente_endpoint(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Eliminar docente"""
    eliminar_docente(db, docente_id)
    return {"mensaje": "Docente eliminado correctamente"}



# ================================================================
#                     DASHBOARD DOCENTE
# ================================================================

# 🔍 Obtener docente del usuario actual
def obtener_docente_por_usuario(db: Session, usuario_id: int):
    return db.query(Docente).filter(Docente.usuario_id == usuario_id).first()


# ------------------------------------------------------------
# 1️⃣ RESUMEN GENERAL DEL DOCENTE
# ------------------------------------------------------------
@router.get("/dashboard/resumen")
def dashboard_resumen(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_docente_por_usuario(db, usuario_actual.id)
    if not docente:
        raise HTTPException(404, "Docente no encontrado")

    estudiantes = db.query(Estudiante).filter(Estudiante.docente_id == docente.id)

    total_estudiantes = estudiantes.count()
    activos = estudiantes.filter(Estudiante.activo == True).count()
    inactivos = total_estudiantes - activos

    total_actividades = db.query(Actividad).count()

    niveles = (
        db.query(Estudiante.nivel_educativo, func.count(Estudiante.id))
        .filter(Estudiante.docente_id == docente.id)
        .group_by(Estudiante.nivel_educativo)
        .all()
    )
    niveles_dict = {f"nivel_{n}": c for n, c in niveles}

    return {
        "total_estudiantes": total_estudiantes,
        "estudiantes_activos": activos,
        "estudiantes_inactivos": inactivos,
        "total_actividades": total_actividades,
        "niveles": niveles_dict
    }


# ------------------------------------------------------------
# 2️⃣ PROGRESO MENSUAL (dummy por ahora)
# ------------------------------------------------------------
@router.get("/dashboard/progreso-mensual")
def progreso_mensual(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    # Luego se conecta a resultados reales
    return [
        {"mes": "Enero", "valor": 45},
        {"mes": "Febrero", "valor": 60},
        {"mes": "Marzo", "valor": 72},
        {"mes": "Abril", "valor": 80},
        {"mes": "Mayo", "valor": 65},
    ]


# ------------------------------------------------------------
# 3️⃣ RENDIMIENTO POR CURSOS (dummy por ahora)
# ------------------------------------------------------------
@router.get("/dashboard/rendimiento-cursos")
def rendimiento_cursos(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return [
        {"curso": "Lectura Inicial", "promedio": 8.4},
        {"curso": "Comprensión 1", "promedio": 7.8},
        {"curso": "Comprensión 2", "promedio": 9.2},
    ]


# ------------------------------------------------------------
# 4️⃣ DISTRIBUCIÓN DE NIVELES (real con BD)
# ------------------------------------------------------------
@router.get("/dashboard/niveles")
def niveles_estudiantes(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_docente_por_usuario(db, usuario_actual.id)
    if not docente:
        raise HTTPException(404, "Docente no encontrado")

    niveles = (
        db.query(Estudiante.nivel_educativo, func.count(Estudiante.id))
        .filter(Estudiante.docente_id == docente.id)
        .group_by(Estudiante.nivel_educativo)
        .all()
    )

    return {f"nivel_{n}": c for n, c in niveles}

