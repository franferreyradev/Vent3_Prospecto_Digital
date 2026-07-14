import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

GTIN_REGEX = re.compile(r"^\d{14}$")


class GtinRegistroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    producto_id: uuid.UUID
    gtin: str
    estado_gtin: str
    es_vigente: bool
    url_digital_link: str | None
    qr_generado: bool
    validado_gs1: bool
    created_at: datetime


class GtinUpdateRequest(BaseModel):
    gtin: str | None = None
    es_vigente: bool | None = None
    url_digital_link: str | None = None
    qr_generado: bool | None = None
    validado_gs1: bool | None = None

    @field_validator("gtin")
    @classmethod
    def validar_formato_gtin(cls, v: str | None) -> str | None:
        if v is not None and not GTIN_REGEX.match(v):
            raise ValueError("El GTIN debe tener exactamente 14 dígitos")
        return v
