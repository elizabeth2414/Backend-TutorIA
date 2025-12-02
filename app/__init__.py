# app/__init__.py

from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Seguridad JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key")  # valor por defecto si no existe
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

settings = Settings()
