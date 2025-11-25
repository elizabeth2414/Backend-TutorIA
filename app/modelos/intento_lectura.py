from sqlalchemy import Column, BigInteger, String, DateTime, Float, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class IntentoLectura(Base):
    __tablename__ = 'intento_lectura'
    
    id = Column(BigInteger, primary_key=True, index=True)
    evaluacion_id = Column(BigInteger, ForeignKey('evaluacion_lectura.id', ondelete='CASCADE'), nullable=False)
    numero_intento = Column(Integer, nullable=False)
    puntuacion_pronunciacion = Column(Float)
    velocidad_lectura = Column(Float)
    fluidez = Column(Float)
    audio_url = Column(String(500))
    fecha_intento = Column(DateTime(timezone=True), server_default=func.now())
    
    evaluacion = relationship("EvaluacionLectura")
    
    __table_args__ = (
        UniqueConstraint('evaluacion_id', 'numero_intento', name='uq_evaluacion_intento'),
        CheckConstraint("numero_intento >= 1", name='check_numero_intento'),
        CheckConstraint("puntuacion_pronunciacion >= 0 AND puntuacion_pronunciacion <= 100", name='check_puntuacion_intento'),
    )