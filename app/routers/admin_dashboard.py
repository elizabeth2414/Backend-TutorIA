from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos.usuario_rol import UsuarioRol
from app.esquemas.dashboard import DashboardStats
from app.servicios.dashboard import obtener_estadisticas_dashboard

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/dashboard", response_model=DashboardStats)
def obtener_dashboard(
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    # 🔍 Consultar roles directamente
    roles = (
        db.query(UsuarioRol.rol)
        .filter(
            UsuarioRol.usuario_id == usuario_actual.id,
            UsuarioRol.activo == True
        )
        .all()
    )

    # roles viene como [('admin',)]
    roles_normalizados = [r[0].upper() for r in roles]

    if "ADMIN" not in roles_normalizados:
        raise HTTPException(
            status_code=403,
            detail="No autorizado"
        )

    return obtener_estadisticas_dashboard(db)
