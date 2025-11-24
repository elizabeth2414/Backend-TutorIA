from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_USER = "postgres"           
DB_PASSWORD = "12345"      
DB_HOST = "localhost"      
DB_PORT = 5432       
DB_NAME = "proyecto_tutor"     


SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    print("✅ Conexión a la base de datos exitosa")
except Exception as e:
    print(f"❌ No se pudo conectar a la base de datos: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()