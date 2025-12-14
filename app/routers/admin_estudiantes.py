from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Estudiante, UsuarioRol

router = APIRouter(prefix="/admin", tags=["Admin Estudiantes"])

@router.get("/estudiantes")
def listar_estudiantes_admin(
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual),
):
    # 🔐 validar ADMIN (sin usar relaciones)
    roles = (
        db.query(UsuarioRol.rol)
        .filter(
            UsuarioRol.usuario_id == usuario_actual.id,
            UsuarioRol.activo == True
        )
        .all()
    )

    roles_normalizados = [r[0].upper() for r in roles]

    if "ADMIN" not in roles_normalizados:
        raise HTTPException(status_code=403, detail="No autorizado")

    estudiantes = (
        db.query(Estudiante)
        .all()
    )

    return estudiantes
