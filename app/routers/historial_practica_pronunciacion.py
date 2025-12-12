from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Estudiante, Padre
from app.modelos.historial_practica_pronunciacion import (
    HistorialPracticaPronunciacion
)
from app.esquemas.historial_practica_pronunciacion import (
    HistorialPracticaPronunciacionResponse
)

router = APIRouter(
    prefix="/historial/practicas",
    tags=["Historial Prácticas Pronunciación"]
)


# =========================================================
# ESTUDIANTE: ver sus prácticas
# =========================================================
@router.get(
    "/mis",
    response_model=List[HistorialPracticaPronunciacionResponse]
)
def obtener_mis_practicas(
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
        db.query(HistorialPracticaPronunciacion)
        .filter(
            HistorialPracticaPronunciacion.estudiante_id == estudiante.id
        )
        .order_by(HistorialPracticaPronunciacion.fecha.desc())
        .all()
    )

    return historial


# =========================================================
# PADRE: ver prácticas de un hijo
# =========================================================
@router.get(
    "/hijo/{estudiante_id}",
    response_model=List[HistorialPracticaPronunciacionResponse]
)
def obtener_practicas_hijo(
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
        raise HTTPException(403, "No autorizado")

    historial = (
        db.query(HistorialPracticaPronunciacion)
        .filter(
            HistorialPracticaPronunciacion.estudiante_id == estudiante.id
        )
        .order_by(HistorialPracticaPronunciacion.fecha.desc())
        .all()
    )

    return historial
