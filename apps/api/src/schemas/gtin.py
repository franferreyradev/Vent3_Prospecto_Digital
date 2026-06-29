import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
