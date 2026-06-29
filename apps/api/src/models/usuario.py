from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, SmallInteger, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base
from src.models.enums import rol_usuario_enum


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(60), nullable=False)
    rol: Mapped[str] = mapped_column(rol_usuario_enum, nullable=False, default="lector")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    intentos_fallidos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    prospectos_subidos: Mapped[list[Prospecto]] = relationship(
        "Prospecto", back_populates="usuario_subio"
    )
    audit_events: Mapped[list[AuditLog]] = relationship(
        "AuditLog", back_populates="usuario"
    )


# Imports tardíos solo para type checkers — en runtime SQLAlchemy usa strings
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.prospecto import Prospecto
    from src.models.audit_log import AuditLog
