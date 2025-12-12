from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Estudiante, Padre
from app.modelos.historial_pronunciacion import HistorialPronunciacion
from app.esquemas.historial_pronunciacion import HistorialPronunciacionResponse

router = APIRouter(
    prefix="/historial/pronunciacion",
    tags=["Historial Pronunciación"]
)


# =========================================================
# ESTUDIANTE: ver su historial de pronunciación
# =========================================================
@router.get(
    "/mis",
    response_model=List[HistorialPronunciacionResponse]
)
def obtener_mi_historial_pronunciacion(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    estudiante = (
        db.query(Estudiante)
        .filter(Estudiante.usuario_id == usuario_actual.id)
        .first()
    )

    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado")

    historial = (
        db.query(HistorialPronunciacion)
        .filter(HistorialPronunciacion.estudiante_id == estudiante.id)
        .order_by(HistorialPronunciacion.fecha.desc())
        .all()
    )

    return historial


# =========================================================
# PADRE: ver historial de un hijo
# =========================================================
@router.get(
    "/hijo/{estudiante_id}",
    response_model=List[HistorialPronunciacionResponse]
)
def obtener_historial_pronunciacion_hijo(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    padre = (
        db.query(Padre)
        .filter(Padre.usuario_id == usuario_actual.id)
        .first()
    )

    if not padre:
        raise HTTPException(403, "Acceso solo para padres")

    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.padre_id == padre.id
        )
        .first()
    )

    if not estudiante:
        raise HTTPException(403, "No autorizado para ver este estudiante")

    historial = (
        db.query(HistorialPronunciacion)
        .filter(HistorialPronunciacion.estudiante_id == estudiante.id)
        .order_by(HistorialPronunciacion.fecha.desc())
        .all()
    )

    return historial
