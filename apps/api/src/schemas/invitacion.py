import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitacionCreateRequest(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=1, max_length=100)
    rol: Literal["admin", "editor"]


class InvitacionCreadaResponse(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str
    rol: str
    expira_en: datetime
    link: str


class InvitacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    nombre: str
    rol: str
    creado_en: datetime
    expira_en: datetime
    usado_en: datetime | None
    estado: Literal["pendiente", "usada", "expirada"]
    # token_hash nunca se expone


class InvitacionValidarResponse(BaseModel):
    email: str
    nombre: str
    rol: str


class InvitacionActivarRequest(BaseModel):
    password: str = Field(min_length=8)
