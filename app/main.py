# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.logs.logger import logger
from app.config import SessionLocal
from app.routers import api_router

# =====================================================
# APP
# =====================================================
app = FastAPI(
    title="Tutor IA - Backend",
    version="1.0.0"
)

logger.info("🚀 Backend TutorIA iniciado correctamente")

# =====================================================
# CORS CONFIG (WEB + ANDROID + JWT)
# =====================================================
# ⚠️ IMPORTANTE:
# - NO usar "*" cuando allow_credentials=True
# - Authorization header cuenta como credencial
# - Capacitor usa diferentes esquemas según plataforma
# =====================================================
origins = [
    # Desarrollo local web
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    
    # Red local (ajusta según tu IP)
    "http://192.168.53.45:5173",
    "http://192.168.100.14:5173",
    
    # Capacitor Android/iOS
    "capacitor://localhost",
    "http://localhost:8080",
    
    # Esquemas adicionales de Capacitor
    "ionic://localhost",
    "http://localhost",
    "https://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Importante para que el frontend vea los headers
)

# =====================================================
# ENDPOINTS DE PRUEBA
# =====================================================
@app.get("/")
def root():
    return {"message": "API TutorIA funcionando correctamente"}

@app.get("/test")
def test():
    logger.info("Se llamó al endpoint /test")
    return {"message": "Todo OK"}

@app.get("/test-db")
def test_db():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"message": "🚀 Conexión a la base de datos exitosa"}
    except SQLAlchemyError as e:
        logger.error(str(e))
        return {
            "message": "❌ Error en la conexión a la base de datos",
            "detail": str(e),
        }

# =====================================================
# REGISTRO DE ROUTERS
# =====================================================
app.include_router(api_router, prefix="/api")

# =====================================================
# MANEJADOR DE ERRORES GLOBAL (opcional pero útil)
# =====================================================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error no manejado: {exc}")
    return {
        "message": "Error interno del servidor",
        "detail": str(exc)
    }