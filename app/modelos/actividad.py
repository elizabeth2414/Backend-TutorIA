from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class Actividad(Base):
    __tablename__ = 'actividad'
    
    id = Column(BigInteger, primary_key=True, index=True)
    contenido_id = Column(BigInteger, ForeignKey('contenido_lectura.id', ondelete='CASCADE'), nullable=False)
    tipo = Column(String(50), nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    configuracion = Column(JSON, nullable=False)
    puntos_maximos = Column(Integer, nullable=False)
    tiempo_estimado = Column(Integer)
    dificultad = Column(Integer)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    contenido = relationship("ContenidoLectura")
    
    __table_args__ = (
        CheckConstraint("tipo IN ('sopa_letras', 'completar_palabras', 'preguntas', 'secuencia', 'verdadero_falso', 'emparejamiento', 'multiple_choice', 'ordenar_oraciones')", name='check_tipo_actividad'),
        CheckConstraint("puntos_maximos > 0", name='check_puntos_maximos'),
        CheckConstraint("dificultad BETWEEN 1 AND 3", name='check_dificultad_actividad'),
    )