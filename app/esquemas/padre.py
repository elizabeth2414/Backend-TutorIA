from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PadreBase(BaseModel):
    telefono_contacto: Optional[str] = None
    parentesco: Optional[str] = None
    notificaciones_activas: bool = True
    activo: bool = True

class PadreCreate(PadreBase):
    usuario_id: Optional[int] = None

class PadreUpdate(BaseModel):
    telefono_contacto: Optional[str] = None
    parentesco: Optional[str] = None
    notificaciones_activas: Optional[bool] = None
    activo: Optional[bool] = None

class PadreResponse(PadreBase):
    id: int
    usuario_id: Optional[int]
    creado_en: datetime
    usuario: Optional['UsuarioResponse'] = None
    
    class Config:
        from_attributes = True

class AccesoPadreBase(BaseModel):
    email_padre: Optional[str] = None
    rol_padre: str = 'padre'
    puede_ver_progreso: bool = True

class AccesoPadreCreate(AccesoPadreBase):
    estudiante_id: int
    padre_id: Optional[int] = None

class AccesoPadreResponse(AccesoPadreBase):
    id: int
    estudiante_id: int
    padre_id: Optional[int]
    creado_en: datetime
    estudiante: Optional['EstudianteResponse'] = None
    padre: Optional['PadreResponse'] = None
    
    class Config:
        from_attributes = True