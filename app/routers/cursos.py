from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import get_db
from app.esquemas.curso import (
    CursoCreate, CursoResponse, CursoUpdate,
    EstudianteCursoCreate, EstudianteCursoResponse
)

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
from app.modelos import Usuario, Docente  # 👈 IMPORTANTE

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
    # 1️⃣ Buscar el docente asociado a este usuario
    docente = (
        db.query(Docente)
        .filter(Docente.usuario_id == usuario_actual.id)
        .first()
    )

    # 2️⃣ Si NO existe, lo creamos automáticamente
    if not docente:
        docente = Docente(
            usuario_id=usuario_actual.id,
            # Los demás campos de Docente son opcionales según tu modelo
            # especialidad=None,
            # grado_academico=None,
            # institucion=None,
            # fecha_contratacion=None,
            activo=True,
        )
        db.add(docente)
        db.commit()
        db.refresh(docente)

    # 3️⃣ Asignar el ID del DOCENTE (NO el del usuario)
    curso.docente_id = docente.id

    # 4️⃣ Crear el curso con el servicio
    return crear_curso(db, curso)


# ================================
#   LISTAR CURSOS
# ================================
@router.get("/", response_model=List[CursoResponse])
def listar_cursos(
    skip: int = 0,
    limit: int = 100,
    docente_id: Optional[int] = None,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    # Si no se envía docente_id, usamos el docente del usuario logueado
    if docente_id is None:
        docente = (
            db.query(Docente)
            .filter(Docente.usuario_id == usuario_actual.id)
            .first()
        )
        if not docente:
            # Si aún no tiene perfil de docente, no hay cursos
            return []
        docente_id = docente.id

    return obtener_cursos(
        db,
        skip=skip,
        limit=limit,
        docente_id=docente_id,
        activo=activo
    )


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
#   ACTUALIZAR CURSO
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
