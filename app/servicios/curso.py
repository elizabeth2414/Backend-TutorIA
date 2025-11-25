from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
import secrets
import string

from app.modelos import Curso, EstudianteCurso
from app.esquemas.curso import CursoCreate, CursoUpdate

def generar_codigo_acceso(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def crear_curso(db: Session, curso: CursoCreate):
    # Generar código de acceso único
    codigo = generar_codigo_acceso()
    while db.query(Curso).filter(Curso.codigo_acceso == codigo).first():
        codigo = generar_codigo_acceso()
    
    db_curso = Curso(**curso.dict(), codigo_acceso=codigo)
    db.add(db_curso)
    db.commit()
    db.refresh(db_curso)
    return db_curso

def obtener_cursos(db: Session, skip: int = 0, limit: int = 100, 
                  docente_id: Optional[int] = None, activo: Optional[bool] = None):
    query = db.query(Curso)
    if docente_id is not None:
        query = query.filter(Curso.docente_id == docente_id)
    if activo is not None:
        query = query.filter(Curso.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_curso(db: Session, curso_id: int):
    return db.query(Curso).filter(Curso.id == curso_id).first()

def obtener_curso_por_codigo(db: Session, codigo_acceso: str):
    return db.query(Curso).filter(Curso.codigo_acceso == codigo_acceso).first()

def actualizar_curso(db: Session, curso_id: int, curso: CursoUpdate):
    db_curso = obtener_curso(db, curso_id)
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    update_data = curso.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_curso, field, value)
    
    db.commit()
    db.refresh(db_curso)
    return db_curso

def eliminar_curso(db: Session, curso_id: int):
    db_curso = obtener_curso(db, curso_id)
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Soft delete
    db_curso.activo = False
    db.commit()
    return db_curso

def inscribir_estudiante(db: Session, curso_id: int, estudiante_id: int):
    # Verificar que el curso existe
    curso = obtener_curso(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Verificar que el estudiante existe
    from app.servicios.estudiante import obtener_estudiante
    estudiante = obtener_estudiante(db, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Verificar que no esté ya inscrito
    existente = db.query(EstudianteCurso).filter(
        EstudianteCurso.curso_id == curso_id,
        EstudianteCurso.estudiante_id == estudiante_id
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante ya está inscrito en este curso"
        )
    
    db_inscripcion = EstudianteCurso(curso_id=curso_id, estudiante_id=estudiante_id)
    db.add(db_inscripcion)
    db.commit()
    db.refresh(db_inscripcion)
    return db_inscripcion

def obtener_estudiantes_curso(db: Session, curso_id: int):
    return db.query(EstudianteCurso).filter(EstudianteCurso.curso_id == curso_id).all()

def obtener_cursos_estudiante(db: Session, estudiante_id: int):
    return db.query(EstudianteCurso).filter(EstudianteCurso.estudiante_id == estudiante_id).all()