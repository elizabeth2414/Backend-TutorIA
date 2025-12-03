from __future__ import annotations   # ← NECESARIO para referencias al mismo archivo

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# IMPORTS CORRECTOS PARA EVITAR EL ERROR
from app.esquemas.docente import DocenteResponse
from app.esquemas.estudiante import EstudianteResponse


# ================================
#   ESQUEMAS PARA CURSO
# ================================
class CursoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    nivel: int
    codigo_acceso: Optional[str] = None
    activo: bool = True
    configuracion: Optional[Dict[str, Any]] = None


class CursoCreate(CursoBase):
    # AHORA ES OPCIONAL → el front NO tiene que enviarlo
    docente_id: Optional[int] = None


class CursoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    nivel: Optional[int] = None
    codigo_acceso: Optional[str] = None
    activo: Optional[bool] = None
    configuracion: Optional[Dict[str, Any]] = None


class CursoResponse(CursoBase):
    id: int
    docente_id: int
    fecha_creacion: datetime
    docente: Optional[DocenteResponse] = None
    
    class Config:
        from_attributes = True


# ================================
#   ESQUEMAS PARA ESTUDIANTE-CURSO
# ================================
class EstudianteCursoBase(BaseModel):
    estado: str = 'activo'


class EstudianteCursoCreate(EstudianteCursoBase):
    estudiante_id: int
    curso_id: int


class EstudianteCursoResponse(EstudianteCursoBase):
    id: int
    estudiante_id: int
    curso_id: int
    fecha_inscripcion: datetime

    estudiante: Optional[EstudianteResponse] = None
    curso: Optional[CursoResponse] = None

    class Config:
        from_attributes = True
