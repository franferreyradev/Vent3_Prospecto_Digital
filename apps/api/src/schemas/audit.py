import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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

    @field_validator("ip_origen", mode="before")
    @classmethod
    def coerce_ip_origen(cls, v: object) -> str | None:
        # La columna INET vuelve de SQLAlchemy/asyncpg como IPv4Address/IPv6Address, no str.
        return str(v) if v is not None else None
