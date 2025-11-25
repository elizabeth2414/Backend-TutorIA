from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

# Esquemas base comunes
class ModeloBase(BaseModel):
    class Config:
        from_attributes = True

class Mensaje(BaseModel):
    mensaje: str