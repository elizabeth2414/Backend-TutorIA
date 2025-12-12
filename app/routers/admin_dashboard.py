from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.esquemas.dashboard import DashboardStats
from app.servicios.dashboard import obtener_estadisticas_dashboard

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/dashboard", response_model=DashboardStats)
def obtener_dashboard(
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    # Normalizar roles
    roles = [r.nombre.upper() for r in usuario_actual.roles]

    if "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="No autorizado")

    datos = obtener_estadisticas_dashboard(db)
    return datos

