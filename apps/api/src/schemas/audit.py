import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tabla_afectada: str
    registro_id: uuid.UUID
    accion: str
    campo_modificado: str | None
    valor_anterior: str | None
    valor_nuevo: str | None
    usuario_id: uuid.UUID
    ip_origen: str | None
    created_at: datetime
