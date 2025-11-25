from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class ActividadBase(BaseModel):
    tipo: str
    titulo: str
    descripcion: Optional[str] = None
    configuracion: Dict[str, Any]
    puntos_maximos: int
    tiempo_estimado: Optional[int] = None
    dificultad: Optional[int] = None
    activo: bool = True

class ActividadCreate(ActividadBase):
    contenido_id: int

class ActividadResponse(ActividadBase):
    id: int
    contenido_id: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class PreguntaBase(BaseModel):
    texto_pregunta: str
    tipo_respuesta: str
    opciones: Optional[Dict[str, Any]] = None
    respuesta_correcta: Optional[str] = None
    puntuacion: int
    explicacion: Optional[str] = None
    orden: int = 1

class PreguntaCreate(PreguntaBase):
    actividad_id: int

class PreguntaResponse(PreguntaBase):
    id: int
    actividad_id: int
    
    class Config:
        from_attributes = True

class ProgresoActividadBase(BaseModel):
    puntuacion: float
    intentos: int = 1
    tiempo_completacion: Optional[int] = None
    errores_cometidos: int = 0
    respuestas: Optional[Dict[str, Any]] = None

class ProgresoActividadCreate(ProgresoActividadBase):
    estudiante_id: int
    actividad_id: int

class ProgresoActividadResponse(ProgresoActividadBase):
    id: int
    estudiante_id: int
    actividad_id: int
    fecha_completacion: datetime
    
    class Config:
        from_attributes = True

class RespuestaPreguntaBase(BaseModel):
    respuesta_estudiante: Optional[str] = None
    correcta: Optional[bool] = None
    puntuacion_obtenida: Optional[int] = None
    tiempo_respuesta: Optional[int] = None

class RespuestaPreguntaCreate(RespuestaPreguntaBase):
    progreso_id: int
    pregunta_id: int

class RespuestaPreguntaResponse(RespuestaPreguntaBase):
    id: int
    progreso_id: int
    pregunta_id: int
    
    class Config:
        from_attributes = True