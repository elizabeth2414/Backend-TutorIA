from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.esquemas import padre as schemas
from app.servicios import padre as services
from app.config.database import get_db

router = APIRouter(prefix="/padres", tags=["Padres"])

@router.post("/", response_model=schemas.PadreResponse)
def crear_padre(padre: schemas.PadreCreate, db: Session = Depends(get_db)):
    return services.crear_padre(db, padre)

@router.get("/", response_model=List[schemas.PadreResponse])
def listar_padres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return services.obtener_padres(db, skip, limit)

@router.get("/{padre_id}", response_model=schemas.PadreResponse)
def obtener_padre(padre_id: int, db: Session = Depends(get_db)):
    db_padre = services.obtener_padre(db, padre_id)
    if not db_padre:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    return db_padre

@router.put("/{padre_id}", response_model=schemas.PadreResponse)
def actualizar_padre(padre_id: int, padre: schemas.PadreUpdate, db: Session = Depends(get_db)):
    return services.actualizar_padre(db, padre_id, padre)

@router.delete("/{padre_id}")
def eliminar_padre(padre_id: int, db: Session = Depends(get_db)):
    services.eliminar_padre(db, padre_id)
    return {"mensaje": "Padre eliminado"}

@router.post("/acceso", response_model=schemas.AccesoPadreResponse)
def crear_acceso_padre(acceso: schemas.AccesoPadreCreate, db: Session = Depends(get_db)):
    return services.crear_acceso_padre(db, acceso)

@router.get("/acceso/{estudiante_id}", response_model=List[schemas.AccesoPadreResponse])
def listar_accesos_estudiante(estudiante_id: int, db: Session = Depends(get_db)):
    return services.obtener_accesos_por_estudiante(db, estudiante_id)