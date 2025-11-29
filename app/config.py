# app/config.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app import settings  # <- viene de app/__init__.py

# URL de la base de datos. Se toma de .env (DATABASE_URL) o del valor por defecto en settings.
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Ejemplo de .env para tu caso (PostgreSQL):
# DATABASE_URL=postgresql+psycopg2://postgres:12345@localhost:5432/proyecto_tutor

engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base para todos los modelos
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI para obtener una sesión de BD por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
