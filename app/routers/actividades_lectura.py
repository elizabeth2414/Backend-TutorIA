# app/routers/actividades_lectura.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import get_db
from app.modelos import Usuario
from app.seguridad.autenticacion import obtener_usuario_actual
from app.esquemas.actividad_lectura import (
    ActividadLecturaCreate,
    ActividadLecturaUpdate,
    ActividadLecturaResponse
)
from app.servicios.actividad_lectura import (
    crear_actividad_lectura,
    obtener_actividades_lectura,
    obtener_actividad_lectura,
    actualizar_actividad_lectura,
    eliminar_actividad_lectura,
    obtener_actividades_por_edad,
    obtener_actividades_generadas_ia
)

router = APIRouter(prefix="/actividades-lectura", tags=["actividades-lectura"])


@router.post("/", response_model=ActividadLecturaResponse, status_code=201)
def crear_actividad(
    actividad: ActividadLecturaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Crear una nueva actividad de lectura.

    Requiere autenticación (docente o admin).
    """
    return crear_actividad_lectura(db, actividad)


@router.get("/", response_model=List[ActividadLecturaResponse])
def listar_actividades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    lectura_id: Optional[int] = Query(None, description="Filtrar por ID de lectura"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de actividad"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Listar actividades de lectura con filtros opcionales.

    Filtros disponibles:
    - lectura_id: ID del contenido de lectura
    - tipo: Tipo de actividad
    - activo: Solo actividades activas o inactivas
    """
    return obtener_actividades_lectura(
        db,
        skip=skip,
        limit=limit,
        lectura_id=lectura_id,
        tipo=tipo,
        activo=activo
    )


@router.get("/edad/{edad_estudiante}", response_model=List[ActividadLecturaResponse])
def listar_actividades_por_edad(
    edad_estudiante: int,
    lectura_id: Optional[int] = Query(None, description="Filtrar por ID de lectura"),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtener actividades apropiadas para la edad del estudiante.

    Filtra automáticamente por edad_min y edad_max.
    """
    return obtener_actividades_por_edad(db, edad_estudiante, lectura_id)


@router.get("/ia", response_model=List[ActividadLecturaResponse])
def listar_actividades_ia(
    lectura_id: Optional[int] = Query(None, description="Filtrar por ID de lectura"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Listar solo las actividades generadas por IA.

    Útil para revisar qué ha generado automáticamente el sistema.
    """
    return obtener_actividades_generadas_ia(db, lectura_id, skip, limit)


@router.get("/{actividad_id}", response_model=ActividadLecturaResponse)
def obtener_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtener una actividad de lectura específica por ID.
    """
    return obtener_actividad_lectura(db, actividad_id)


@router.put("/{actividad_id}", response_model=ActividadLecturaResponse)
def actualizar_actividad(
    actividad_id: int,
    actividad: ActividadLecturaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Actualizar una actividad de lectura existente.

    Solo se actualizan los campos proporcionados.
    Requiere autenticación (docente o admin).
    """
    return actualizar_actividad_lectura(db, actividad_id, actividad)


@router.delete("/{actividad_id}")
def desactivar_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Desactivar una actividad de lectura (soft delete).

    La actividad no se elimina físicamente, solo se marca como inactiva.
    Requiere autenticación (docente o admin).
    """
    return eliminar_actividad_lectura(db, actividad_id)
