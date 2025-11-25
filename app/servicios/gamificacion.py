from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date

from app.modelos import Recompensa, RecompensaEstudiante, MisionDiaria, HistorialPuntos, NivelEstudiante
from app.esquemas.gamificacion import RecompensaCreate, RecompensaEstudianteCreate, MisionDiariaCreate, HistorialPuntosCreate

def crear_recompensa(db: Session, recompensa: RecompensaCreate):
    db_recompensa = Recompensa(**recompensa.dict())
    db.add(db_recompensa)
    db.commit()
    db.refresh(db_recompensa)
    return db_recompensa

def obtener_recompensas(db: Session, skip: int = 0, limit: int = 100, activo: Optional[bool] = None):
    query = db.query(Recompensa)
    if activo is not None:
        query = query.filter(Recompensa.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_recompensa(db: Session, recompensa_id: int):
    return db.query(Recompensa).filter(Recompensa.id == recompensa_id).first()

def asignar_recompensa_estudiante(db: Session, asignacion: RecompensaEstudianteCreate):
    # Verificar si ya tiene la recompensa
    existente = db.query(RecompensaEstudiante).filter(
        RecompensaEstudiante.estudiante_id == asignacion.estudiante_id,
        RecompensaEstudiante.recompensa_id == asignacion.recompensa_id
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante ya tiene esta recompensa"
        )
    
    db_asignacion = RecompensaEstudiante(**asignacion.dict())
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def obtener_recompensas_estudiante(db: Session, estudiante_id: int):
    return db.query(RecompensaEstudiante).filter(RecompensaEstudiante.estudiante_id == estudiante_id).all()

def crear_mision_diaria(db: Session, mision: MisionDiariaCreate):
    db_mision = MisionDiaria(**mision.dict())
    db.add(db_mision)
    db.commit()
    db.refresh(db_mision)
    return db_mision

def obtener_misiones_estudiante(db: Session, estudiante_id: int, fecha: Optional[str] = None):
    query = db.query(MisionDiaria).filter(MisionDiaria.estudiante_id == estudiante_id)
    if fecha:
        query = query.filter(MisionDiaria.fecha == fecha)
    return query.all()

def actualizar_progreso_mision(db: Session, mision_id: int, progreso: int):
    db_mision = db.query(MisionDiaria).filter(MisionDiaria.id == mision_id).first()
    if not db_mision:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    
    db_mision.progreso = progreso
    if progreso >= db_mision.objetivo:
        db_mision.completada = True
    
    db.commit()
    db.refresh(db_mision)
    return db_mision

def agregar_puntos_estudiante(db: Session, puntos: HistorialPuntosCreate):
    db_puntos = HistorialPuntos(**puntos.dict())
    db.add(db_puntos)
    
    # Actualizar el nivel del estudiante
    nivel_estudiante = db.query(NivelEstudiante).filter(
        NivelEstudiante.estudiante_id == puntos.estudiante_id
    ).first()
    
    if nivel_estudiante:
        nivel_estudiante.puntos_totales += puntos.puntos
        nivel_estudiante.puntos_nivel_actual += puntos.puntos
        
        # Lógica para subir de nivel
        if nivel_estudiante.puntos_nivel_actual >= nivel_estudiante.puntos_para_siguiente_nivel:
            nivel_estudiante.nivel_actual += 1
            nivel_estudiante.puntos_nivel_actual = 0
            nivel_estudiante.puntos_para_siguiente_nivel = nivel_estudiante.nivel_actual * 1000
    
    db.commit()
    db.refresh(db_puntos)
    return db_puntos

def obtener_historial_puntos_estudiante(db: Session, estudiante_id: int, skip: int = 0, limit: int = 50):
    return db.query(HistorialPuntos).filter(
        HistorialPuntos.estudiante_id == estudiante_id
    ).offset(skip).limit(limit).all()