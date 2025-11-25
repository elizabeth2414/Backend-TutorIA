from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.esquemas.docente import DocenteCreate, DocenteResponse, DocenteUpdate
from app.servicios.docente import (
    crear_docente, obtener_docentes, obtener_docente,
    actualizar_docente, eliminar_docente
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/docentes", tags=["docentes"])

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
def actualizar_docente(
    docente_id: int,
    docente: DocenteUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar docente"""
    return actualizar_docente(db, docente_id, docente)

@router.delete("/{docente_id}")
def eliminar_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Eliminar docente"""
    eliminar_docente(db, docente_id)
    return {"mensaje": "Docente eliminado correctamente"}