from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base
from src.models.enums import estado_vigencia_enum, tipo_audiencia_enum


class Prospecto(Base):
    __tablename__ = "prospectos"
    __table_args__ = (UniqueConstraint("numero_expediente", "version", "tipo_audiencia"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero_expediente: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tipo_audiencia: Mapped[str] = mapped_column(
        tipo_audiencia_enum, nullable=False, default="unico"
    )
    url_archivo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_archivo: Mapped[str] = mapped_column(String(200), nullable=False)
    estado_vigencia: Mapped[str] = mapped_column(
        estado_vigencia_enum, nullable=False, default="en_revision"
    )
    subido_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    usuario_subio: Mapped[Usuario] = relationship("Usuario", back_populates="prospectos_subidos")
    productos_asociados: Mapped[list[ProductoProspecto]] = relationship(
        "ProductoProspecto", back_populates="prospecto"
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.usuario import Usuario
    from src.models.producto_prospecto import ProductoProspecto
