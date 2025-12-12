# app/routers/padres.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.modelos import Estudiante, Padre, ContenidoLectura, Actividad, Usuario
from app.servicios.seguridad import obtener_usuario_actual

from app.servicios.padre_hijos import obtener_hijos_con_cursos
from app.esquemas.padre_hijos import EstudianteConCursosResponse

from app.esquemas.padre import PadreResponse, PadreCreate, PadreUpdate, VincularHijoRequest
from app.servicios.padre import crear_padre, obtener_padres, obtener_padre as obtener_padre_service

from app.servicios.estudiante import obtener_cursos_estudiante


router = APIRouter(prefix="/padres", tags=["Padres"])


# ============================================================
# 1. LISTAR HIJOS DEL PADRE (CORRECTO)
# ============================================================
@router.get("/mis-hijos", response_model=List[EstudianteConCursosResponse])
def listar_hijos_con_cursos(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return obtener_hijos_con_cursos(db, usuario_actual.id)


# ============================================================
# 2. CRUD PADRES
# ============================================================
@router.post("/", response_model=PadreResponse)
def crear_padre_route(padre: PadreCreate, db: Session = Depends(get_db)):
    return crear_padre(db, padre)


@router.get("/", response_model=List[PadreResponse])
def listar_padres_route(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return obtener_padres(db, skip, limit)


@router.get("/{padre_id}", response_model=PadreResponse)
def obtener_padre_route(padre_id: int, db: Session = Depends(get_db)):
    db_padre = obtener_padre_service(db, padre_id)
    if not db_padre:
        raise HTTPException(404, "Padre no encontrado")
    return db_padre


# ============================================================
# 3. VINCULAR HIJO
# ============================================================
@router.post("/vincular-hijo", response_model=dict)
def vincular_hijo(
    data: VincularHijoRequest,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()

    if not padre:
        raise HTTPException(400, "No existe registro de padre.")

    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.nombre.ilike(data.nombre),
            Estudiante.apellido.ilike(data.apellido),
            Estudiante.fecha_nacimiento == data.fecha_nacimiento,
        )
        .first()
    )

    if not estudiante:
        raise HTTPException(404, "No se encontró un estudiante con esos datos.")

    if estudiante.padre_id is not None:
        raise HTTPException(400, "Este estudiante ya tiene un padre asignado.")

    estudiante.padre_id = padre.id
    db.commit()
    db.refresh(estudiante)

    return {"mensaje": "Hijo vinculado correctamente"}


# ============================================================
# 4. LECTURAS DEL HIJO
# ============================================================
# app/routers/padres.py

@router.get("/hijos/{hijo_id}/lecturas")
def obtener_lecturas_hijo(
    hijo_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()
    if not padre:
        raise HTTPException(403, "No existe registro de padre para este usuario.")

    estudiante = db.query(Estudiante).filter(Estudiante.id == hijo_id).first()
    if not estudiante:
        raise HTTPException(404, "El estudiante no existe.")

    if estudiante.padre_id != padre.id:
        raise HTTPException(403, "No puedes ver lecturas de otro estudiante.")

    cursos = obtener_cursos_estudiante(db, hijo_id)
    if not cursos:
        return []

    lecturas_finales = []

    for curso in cursos:
        lecturas = (
            db.query(ContenidoLectura)
            .filter(ContenidoLectura.curso_id == curso.id)
            .all()
        )

        for lectura in lecturas:
            actividades = (
                db.query(Actividad)
                .filter(Actividad.contenido_id == lectura.id)
                .all()
            )

            lecturas_finales.append(
                {
                    "id": lectura.id,
                    "titulo": lectura.titulo,
                    "contenido": lectura.contenido,
                    "curso": curso.nombre,
                    "nivel_dificultad": lectura.nivel_dificultad,
                    "edad_recomendada": lectura.edad_recomendada,
                    "actividades": [
                        {
                            "id": act.id,
                            "tipo": act.tipo,
                            "titulo": act.titulo,
                            "puntos_maximos": act.puntos_maximos,
                        }
                        for act in actividades
                    ],
                }
            )

    return lecturas_finales
