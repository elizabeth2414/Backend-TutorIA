# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import SessionLocal
from app.routers import api_router
from app.routers import api_router


app = FastAPI(title="Tutor IA - Backend")

@app.get("/test-db")
def test_db():
    """
    Endpoint para verificar la conexión a la base de datos.
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        return {"message": "🚀 Conexión a la base de datos exitosa"}
    except SQLAlchemyError as e:
        return {
            "message": "❌ Error en la conexión a la base de datos",
            "detail": str(e),
        }

# CORS: agrega aquí tus frontends reales
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

# Registramos todos los routers (auth, usuarios, cursos, IA, etc.)
app.include_router(api_router, prefix="/api")


