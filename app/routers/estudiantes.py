from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.estudiante import (
    EstudianteCreate, EstudianteResponse, EstudianteUpdate,
    NivelEstudianteResponse
)
from app.servicios.estudiante import (
    crear_estudiante, obtener_estudiantes, obtener_estudiante,
    actualizar_estudiante, eliminar_estudiante, obtener_nivel_estudiante
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/estudiantes", tags=["estudiantes"])

@router.post("/", response_model=EstudianteResponse)
def crear_nuevo_estudiante(
    estudiante: EstudianteCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nuevo estudiante"""
    return crear_estudiante(db, estudiante)

@router.get("/", response_model=List[EstudianteResponse])
def listar_estudiantes(
    skip: int = 0,
    limit: int = 100,
    docente_id: int = None,
    activo: bool = True,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar estudiantes"""
    return obtener_estudiantes(db, skip=skip, limit=limit, docente_id=docente_id, activo=activo)

@router.get("/{estudiante_id}", response_model=EstudianteResponse)
def obtener_estudiante_por_id(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener estudiante por ID"""
    db_estudiante = obtener_estudiante(db, estudiante_id)
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return db_estudiante

@router.put("/{estudiante_id}", response_model=EstudianteResponse)
def actualizar_estudiante(
    estudiante_id: int,
    estudiante: EstudianteUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar estudiante"""
    return actualizar_estudiante(db, estudiante_id, estudiante)

@router.delete("/{estudiante_id}")
def eliminar_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Eliminar estudiante (soft delete)"""
    eliminar_estudiante(db, estudiante_id)
    return {"mensaje": "Estudiante eliminado correctamente"}

@router.get("/{estudiante_id}/nivel", response_model=NivelEstudianteResponse)
def obtener_nivel(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener nivel y progreso del estudiante"""
    return obtener_nivel_estudiante(db, estudiante_id)