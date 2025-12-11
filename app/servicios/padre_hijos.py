# app/servicios/padre_hijos.py
from sqlalchemy.orm import Session

from app.modelos import Padre, Estudiante, EstudianteCurso
from app.esquemas.estudiante import EstudianteResponse
from app.esquemas.curso import CursoResponse
from app.esquemas.padre_hijos import EstudianteConCursosResponse


def obtener_hijos_con_cursos(db: Session, usuario_id: int):

    padre = (
        db.query(Padre)
        .filter(Padre.usuario_id == usuario_id)
        .first()
    )

    if not padre:
        return []

    hijos = (
        db.query(Estudiante)
        .filter(Estudiante.padre_id == padre.id)
        .all()
    )

    resultado = []

    for hijo in hijos:

        relaciones = (
            db.query(EstudianteCurso)
            .filter(EstudianteCurso.estudiante_id == hijo.id)
            .all()
        )

        cursos = [
            CursoResponse.model_validate(rel.curso)
            for rel in relaciones
            if rel.curso
        ]

        resultado.append(
            EstudianteConCursosResponse(
                estudiante=EstudianteResponse.model_validate(hijo),
                cursos=cursos
            )
        )

    return resultado
