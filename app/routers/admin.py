# app/routers/admin.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_db
from app.modelos import Usuario
from app.esquemas.docente import (
    DocenteCreateAdmin,
    DocenteAdminResponse,
    DocenteUpdate,
)
from app.servicios.seguridad import requiere_admin
from app.servicios.docente_admin import (
    crear_docente_admin,
    listar_docentes_admin,
    obtener_docente_admin,
    actualizar_docente_admin,
    desactivar_docente_admin,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ==============================
#   CREAR DOCENTE (ADMIN)
# ==============================

@router.post(
    "/docentes",
    response_model=DocenteAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_docente_desde_admin(
    data: DocenteCreateAdmin,
    db: Session = Depends(get_db),
    usuario_admin: Usuario = Depends(requiere_admin),
):
    """
    Crea:
      - usuario
      - rol 'docente'
      - registro en docente
    SOLO accesible por ADMIN.
    """
    docente = crear_docente_admin(db, data)
    return docente


# ==============================
#   LISTAR DOCENTES
# ==============================

@router.get(
    "/docentes",
    response_model=List[DocenteAdminResponse],
)
def listar_docentes_desde_admin(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    usuario_admin: Usuario = Depends(requiere_admin),
):
    """
    Lista docentes. Puedes filtrar por ?activo=true o ?activo=false
    """
    docentes = listar_docentes_admin(db, activo=activo)
    return docentes


# ==============================
#   OBTENER DOCENTE POR ID
# ==============================

@router.get(
    "/docentes/{docente_id}",
    response_model=DocenteAdminResponse,
)
def obtener_docente_desde_admin(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_admin: Usuario = Depends(requiere_admin),
):
    docente = obtener_docente_admin(db, docente_id)
    return docente


# ==============================
#   ACTUALIZAR DOCENTE
# ==============================

@router.put(
    "/docentes/{docente_id}",
    response_model=DocenteAdminResponse,
)
def actualizar_docente_desde_admin(
    docente_id: int,
    data: DocenteUpdate,
    db: Session = Depends(get_db),
    usuario_admin: Usuario = Depends(requiere_admin),
):
    docente = actualizar_docente_admin(db, docente_id, data)
    return docente


# ==============================
#   DESACTIVAR DOCENTE
# ==============================

@router.delete(
    "/docentes/{docente_id}",
    status_code=status.HTTP_200_OK,
)
def desactivar_docente_desde_admin(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_admin: Usuario = Depends(requiere_admin),
):
    docente = desactivar_docente_admin(db, docente_id)
    return {
        "mensaje": "Docente desactivado correctamente",
        "docente_id": docente.id,
    }
