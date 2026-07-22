from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base
from src.models.enums import rol_usuario_enum


class InvitacionUsuario(Base):
    __tablename__ = "invitaciones_usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[str] = mapped_column(rol_usuario_enum, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    creado_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    expira_en: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    usado_en: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    usuario_creado_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    admin_creador: Mapped[Usuario] = relationship(
        "Usuario", foreign_keys=[creado_por]
    )
    usuario_creado: Mapped[Usuario | None] = relationship(
        "Usuario", foreign_keys=[usuario_creado_id]
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.usuario import Usuario
