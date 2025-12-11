from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from app.modelos import Usuario, UsuarioRol, Padre


from app.config import get_db
from app.esquemas.auth import (
    LoginRequest, Token, UsuarioCreate, UsuarioResponse, 
    CambioPassword, ResetPasswordRequest, ResetPasswordConfirm
)
from app.servicios.auth import (
    autenticar_usuario, crear_usuario, obtener_usuario_actual,
    cambiar_password, crear_token_acceso, resetear_password,
    confirmar_reset_password
)
from app.servicios.seguridad import (
    verificar_token_acceso,
    verificar_password,
    obtener_password_hash,
    asignar_rol
)

from app.modelos import Usuario

router = APIRouter(prefix="/auth", tags=["autenticacion"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/registro", response_model=UsuarioResponse)
def registro(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario"""
    db_usuario = crear_usuario(db, usuario)
    return db_usuario

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Iniciar sesión y obtener token"""
    usuario = autenticar_usuario(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = crear_token_acceso(
        data={"sub": usuario.email, "id": usuario.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.total_seconds()
    }

@router.post("/cambio-password")
def cambio_password(
    cambio: CambioPassword,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Cambiar contraseña del usuario actual"""
    return cambiar_password(db, usuario_actual.id, cambio)

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Solicitar reseteo de contraseña"""
    return resetear_password(db, request.email)

@router.post("/confirm-reset-password")
def confirm_reset_password(request: ResetPasswordConfirm, db: Session = Depends(get_db)):
    """Confirmar reseteo de contraseña con token"""
    return confirmar_reset_password(db, request.token, request.nuevo_password)

@router.get("/me", response_model=UsuarioResponse)
def me(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """Obtener información del usuario actual con sus roles"""

    # Sacamos los roles desde la tabla usuario_rol
    roles_rows = (
        db.query(UsuarioRol.rol)
        .filter(
            UsuarioRol.usuario_id == usuario_actual.id,
            UsuarioRol.activo == True,
        )
        .all()
    )
    roles = [r[0] for r in roles_rows]  # ['admin', 'docente', ...]

    # Construimos manualmente el UsuarioResponse
    return UsuarioResponse(
        id=usuario_actual.id,
        email=usuario_actual.email,
        nombre=usuario_actual.nombre,
        apellido=usuario_actual.apellido,
        activo=usuario_actual.activo,
        fecha_creacion=usuario_actual.fecha_creacion,
        ultimo_login=usuario_actual.ultimo_login,
        bloqueado=usuario_actual.bloqueado,
        roles=roles,
    )

@router.post("/registro-padre", response_model=UsuarioResponse)
def registro_padre(
    datos: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Registra un usuario con rol PADRE y crea su registro en la tabla 'padre'.
    """

    # 1️⃣ Crear usuario
    nuevo_usuario = crear_usuario(db, datos)

    if not nuevo_usuario:
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el usuario padre."
        )

    # 2️⃣ Asignar rol PADRE (ya será convertido a minúsculas por la función)
    asignar_rol(db, nuevo_usuario.id, "padre")

    # 3️⃣ Crear registro en tabla PADRE
    nuevo_padre = Padre(
        usuario_id=nuevo_usuario.id,
        parentesco="padre",
        notificaciones_activas=True
    )

    db.add(nuevo_padre)
    db.commit()
    db.refresh(nuevo_padre)

    return nuevo_usuario
