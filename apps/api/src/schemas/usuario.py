import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    nombre: str
    rol: str
    activo: bool
    ultimo_acceso: datetime | None
    created_at: datetime
    # password_hash, intentos_fallidos y bloqueado_hasta nunca se exponen


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
