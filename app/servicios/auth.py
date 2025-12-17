from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta

from app import settings
from app.modelos import Usuario, UsuarioRol
from app.esquemas.auth import UsuarioCreate, CambioPassword
from app.servicios.seguridad import (
    verificar_password, obtener_password_hash
)


def autenticar_usuario(db: Session, email: str, password: str):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return False
    if not verificar_password(password, usuario.password_hash):
        return False
    return usuario

def crear_usuario(db: Session, usuario: UsuarioCreate):
    # Verificar si el usuario ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    hashed_password = obtener_password_hash(usuario.password)
    db_usuario = Usuario(
        email=usuario.email,
        password_hash=hashed_password,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        activo=usuario.activo
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def cambiar_password(db: Session, usuario_id: int, cambio: CambioPassword):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar contraseña actual
    if not verificar_password(cambio.password_actual, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    usuario.password_hash = obtener_password_hash(cambio.nuevo_password)
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}

def resetear_password(db: Session, email: str):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        # Por seguridad, no revelamos si el email existe
        return {"mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña"}
    
    # Aquí se implementaría el envío de email con token de reseteo
    # Por ahora solo devolvemos un mensaje
    return {"mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña"}

def confirmar_reset_password(db: Session, token: str, nuevo_password: str):
    # Aquí se verificaría el token y se resetearía la contraseña
    # Implementación simplificada
    return {"mensaje": "Contraseña restablecida correctamente"}