import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProspectoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero_expediente: str
    version: int
    tipo_audiencia: str
    url_archivo: str
    nombre_archivo: str
    estado_vigencia: str
    created_at: datetime


class ProspectoCreateRequest(BaseModel):
    numero_expediente: str = Field(max_length=30)
    version: int = Field(ge=1)
    tipo_audiencia: Literal["publico_general", "profesional_salud", "unico"]
    producto_id: uuid.UUID
    # El PDF llega como UploadFile en multipart — no va en este schema


class ProspectoActivarResponse(BaseModel):
    activado: ProspectoResponse
    reemplazado: ProspectoResponse | None = None
