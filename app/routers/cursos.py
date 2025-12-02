from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.curso import (
    CursoCreate, CursoResponse, CursoUpdate,
    EstudianteCursoCreate, EstudianteCursoResponse
)

# IMPORTAMOS LA FUNCIÓN DEL SERVICIO CON ALIAS PARA EVITAR RECURSIÓN
from app.servicios.curso import (
    crear_curso,
    obtener_cursos,
    obtener_curso,
    actualizar_curso as actualizar_curso_service,
    eliminar_curso as eliminar_curso_service,
    inscribir_estudiante,
    obtener_estudiantes_curso,
    obtener_cursos_estudiante
)

from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/cursos", tags=["cursos"])


# ================================
#   CREAR CURSO
# ================================
@router.post("/", response_model=CursoResponse)
def crear_nuevo_curso(
    curso: CursoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    # Asignar automáticamente el docente_id
    curso.docente_id = usuario_actual.id
    return crear_curso(db, curso)


# ================================
#   LISTAR CURSOS
# ================================
@router.get("/", response_model=List[CursoResponse])
def listar_cursos(
    skip: int = 0,
    limit: int = 100,
    docente_id: int = None,
    activo: bool = True,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return obtener_cursos(db, skip=skip, limit=limit, docente_id=docente_id, activo=activo)


# ================================
#   OBTENER CURSO POR ID
# ================================
@router.get("/{curso_id}", response_model=CursoResponse)
def obtener_curso_por_id(
    curso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    db_curso = obtener_curso(db, curso_id)
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return db_curso


# ================================
#   ACTUALIZAR CURSO (CORREGIDO)
# ================================
@router.put("/{curso_id}", response_model=CursoResponse)
def actualizar_curso_router(
    curso_id: int,
    curso: CursoUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return actualizar_curso_service(db, curso_id, curso)


# ================================
#   ELIMINAR CURSO
# ================================
@router.delete("/{curso_id}")
def eliminar_curso_router(
    curso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    eliminar_curso_service(db, curso_id)
    return {"mensaje": "Curso eliminado correctamente"}


# ================================
#   INSCRIBIR ESTUDIANTE
# ================================
@router.post("/{curso_id}/inscribir", response_model=EstudianteCursoResponse)
def inscribir_estudiante_curso(
    curso_id: int,
    inscripcion: EstudianteCursoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return inscribir_estudiante(db, curso_id, inscripcion.estudiante_id)


# ================================
#   LISTAR ESTUDIANTES DEL CURSO
# ================================
@router.get("/{curso_id}/estudiantes", response_model=List[EstudianteCursoResponse])
def listar_estudiantes_curso(
    curso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return obtener_estudiantes_curso(db, curso_id)


# ================================
#   LISTAR CURSOS DE UN ESTUDIANTE
# ================================
@router.get("/estudiante/{estudiante_id}", response_model=List[CursoResponse])
def listar_cursos_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return obtener_cursos_estudiante(db, estudiante_id)
