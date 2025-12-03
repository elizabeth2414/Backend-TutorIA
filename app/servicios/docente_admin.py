# app/servicios/docente_admin.py

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modelos import Usuario, UsuarioRol, Docente
from app.esquemas.docente import (
    DocenteCreateAdmin,
    DocenteAdminResponse,
    DocenteUpdate,
)
from app.servicios.seguridad import get_password_hash


# ==============================
#   CREAR DOCENTE (ADMIN)
# ==============================

def crear_docente_admin(db: Session, data: DocenteCreateAdmin) -> Docente:
    """
    Crea:
      - Usuario
      - Rol 'docente'
      - Registro en tabla docente
    """

    # 1) Verificar que no exista ya el email
    existe = db.query(Usuario).filter(Usuario.email == data.email).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email",
        )

    try:
        # 2) Crear usuario
        usuario = Usuario(
            email=data.email,
            password_hash=get_password_hash(data.password),
            nombre=data.nombre,
            apellido=data.apellido,
            activo=True,
        )
        db.add(usuario)
        db.flush()  # para tener usuario.id sin hacer commit todavía

        # 3) Asignar rol 'docente'
        rol_docente = UsuarioRol(
            usuario_id=usuario.id,
            rol="docente",
            activo=True,
        )
        db.add(rol_docente)

        # 4) Crear registro en docente
        docente = Docente(
            usuario_id=usuario.id,
            especialidad=data.especialidad,
            grado_academico=data.grado_academico,
            institucion=data.institucion,
            fecha_contratacion=data.fecha_contratacion,
            activo=data.activo,
        )
        db.add(docente)

        # 5) Guardar todo
        db.commit()
        db.refresh(docente)

        # Cargar relación usuario para la respuesta
        _ = docente.usuario  # acceso para asegurar lazy load si lo necesitas

        return docente

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear docente: {str(e)}",
        )


# ==============================
#   LISTAR DOCENTES
# ==============================

def listar_docentes_admin(
    db: Session,
    activo: Optional[bool] = None,
) -> List[Docente]:
    """
    Lista docentes, opcionalmente filtrando por activo/inactivo
    """
    query = db.query(Docente).join(Usuario, Docente.usuario_id == Usuario.id)

    if activo is not None:
        query = query.filter(Docente.activo == activo)

    # Si quieres que salgan solo usuarios activos:
    # query = query.filter(Usuario.activo == True)

    return query.all()


# ==============================
#   OBTENER DOCENTE POR ID
# ==============================

def obtener_docente_admin(db: Session, docente_id: int) -> Docente:
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado",
        )
    return docente


# ==============================
#   ACTUALIZAR DOCENTE
# ==============================

def actualizar_docente_admin(
    db: Session,
    docente_id: int,
    data: DocenteUpdate,
) -> Docente:
    docente = obtener_docente_admin(db, docente_id)

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(docente, field, value)

    db.commit()
    db.refresh(docente)
    return docente


# ==============================
#   DESACTIVAR DOCENTE
# ==============================

def desactivar_docente_admin(db: Session, docente_id: int) -> Docente:
    docente = obtener_docente_admin(db, docente_id)

    docente.activo = False

    # Opcional: también desactivar el usuario asociado
    if docente.usuario:
        docente.usuario.activo = False

    db.commit()
    db.refresh(docente)
    return docente
