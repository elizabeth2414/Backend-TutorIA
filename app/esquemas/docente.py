from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from app.esquemas.usuario import UsuarioResponse


class DocenteBase(BaseModel):
    especialidad: Optional[str] = None
    grado_academico: Optional[str] = None
    institucion: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    activo: bool = True

class DocenteCreate(DocenteBase):
    usuario_id: int

class DocenteUpdate(BaseModel):
    especialidad: Optional[str] = None
    grado_academico: Optional[str] = None
    institucion: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    activo: Optional[bool] = None

class DocenteResponse(DocenteBase):
    id: int
    usuario_id: int
    creado_en: datetime
    usuario: Optional['UsuarioResponse'] = None
    
    class Config:
        from_attributes = True