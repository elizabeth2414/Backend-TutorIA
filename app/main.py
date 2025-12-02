# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from app.logs.logger import logger

from app.config import SessionLocal
from app.routers import api_router     # <-- Import correcto

app = FastAPI(title="Tutor IA - Backend")


@app.get("/test")
def test():
    logger.info("Se llamó al endpoint /test")
    return {"message": "Todo OK"}


@app.get("/test-db")
def test_db():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        return {"message": "🚀 Conexión a la base de datos exitosa"}
    except SQLAlchemyError as e:
        return {
            "message": "❌ Error en la conexión a la base de datos",
            "detail": str(e),
        }


# ------------------------------
# CORS CONFIG
# ------------------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------
# REGISTRO DE ROUTERS
# ------------------------------
app.include_router(api_router, prefix="/api")
