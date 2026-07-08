from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base
from src.models.enums import accion_audit_enum


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tabla_afectada: Mapped[str] = mapped_column(String(50), nullable=False)
    registro_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    accion: Mapped[str] = mapped_column(accion_audit_enum, nullable=False)
    campo_modificado: Mapped[str | None] = mapped_column(String(80), nullable=True)
    valor_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_nuevo: Mapped[str | None] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # INET en PostgreSQL — SQLAlchemy/asyncpg devuelve IPv4Address/IPv6Address, no str
    # (coerción a str vive en AuditLogResponse.coerce_ip_origen, apps/api/src/schemas/audit.py)
    ip_origen: Mapped[str | None] = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones — solo INSERT/SELECT; el trigger de DB bloquea UPDATE y DELETE
    usuario: Mapped[Usuario] = relationship("Usuario", back_populates="audit_events")


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.usuario import Usuario
