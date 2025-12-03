# app/servicios/seguridad.py

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import settings
from app.config import get_db
from app.modelos import Usuario, UsuarioRol  # 👈 IMPORTANTE: añadimos UsuarioRol

# ==============================
# CONFIGURACIÓN DE SEGURIDAD
# ==============================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ojo: este tokenUrl es el endpoint de login que ya tienes definido.
# Si tu router de auth está con prefix="/auth" y lo incluyes con prefix="/api",
# el endpoint real será /api/auth/login, pero aquí puede quedar "auth/login"
# porque solo se usa para la documentación de OpenAPI.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ==============================
# HASH / VERIFICACIÓN DE PASSWORD
# ==============================

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Alias para reutilizar en otros módulos (como docente_admin.py)
def get_password_hash(password: str) -> str:
    return obtener_password_hash(password)


# ==============================
# MANEJO DE TOKENS JWT
# ==============================

def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Por defecto 15 minutos
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verificar_token_acceso(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ==============================
# OBTENER USUARIO ACTUAL
# ==============================

async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verificar_token_acceso(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception

    return usuario


# ==============================
# RESTRICCIÓN POR ROL: ADMIN
# ==============================

def requiere_admin(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Verifica que el usuario autenticado tenga rol 'admin'.
    Se usa como dependencia en los endpoints de administración.
    """
    tiene_admin = (
        db.query(UsuarioRol)
        .filter(
            UsuarioRol.usuario_id == usuario.id,
            UsuarioRol.rol == "admin",
            UsuarioRol.activo == True,
        )
        .first()
    )

    if not tiene_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador",
        )

    return usuario
