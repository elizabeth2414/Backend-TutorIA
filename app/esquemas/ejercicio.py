from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EjercicioPracticaBase(BaseModel):
    tipo_ejercicio: str
    palabras_objetivo: List[str]
    texto_practica: str
    dificultad: Optional[int] = None
    completado: bool = False
    intentos: int = 0

class EjercicioPracticaCreate(EjercicioPracticaBase):
    estudiante_id: int
    evaluacion_id: int

class EjercicioPracticaResponse(EjercicioPracticaBase):
    id: int
    estudiante_id: int
    evaluacion_id: int
    fecha_creacion: datetime
    fecha_completacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ResultadoEjercicioBase(BaseModel):
    puntuacion: Optional[float] = None
    audio_url: Optional[str] = None
    retroalimentacion_ia: Optional[str] = None
    errores_corregidos: int = 0
    tiempo_practica: Optional[int] = None

class ResultadoEjercicioCreate(ResultadoEjercicioBase):
    ejercicio_id: int

class ResultadoEjercicioResponse(ResultadoEjercicioBase):
    id: int
    ejercicio_id: int
    fecha_completacion: datetime
    
    class Config:
        from_attributes = True

class FragmentoPracticaBase(BaseModel):
    texto_fragmento: str
    posicion_inicio: int
    posicion_fin: int
    tipo_error_asociado: Optional[str] = None
    completado: bool = False
    mejora_lograda: bool = False

class FragmentoPracticaCreate(FragmentoPracticaBase):
    ejercicio_id: int

class FragmentoPracticaResponse(FragmentoPracticaBase):
    id: int
    ejercicio_id: int
    
    class Config:
        from_attributes = True