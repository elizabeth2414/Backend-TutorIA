from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from app.config import SessionLocal

app = FastAPI()

@app.get("/test-db")
def test_db():
    """
    Endpoint para verificar la conexión a la base de datos.
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")  # consulta mínima
        db.close()
        return {
            "message": "🚀 Conexión a la base de datos exitosa"
        }
    except SQLAlchemyError as e:
        return {
            "message": "❌ Error en la conexión a la base de datos",
            "detail": str(e)
        }
