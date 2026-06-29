from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CHAR, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base
from src.models.enums import estado_gtin_enum


class GtinRegistro(Base):
    __tablename__ = "gtin_registro"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    gtin: Mapped[str] = mapped_column(CHAR(14), nullable=False, unique=True)
    estado_gtin: Mapped[str] = mapped_column(
        estado_gtin_enum, nullable=False, default="en_desarrollo"
    )
    es_vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    url_digital_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_generado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validado_gs1: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    producto: Mapped[Producto] = relationship("Producto", back_populates="gtin_registros")


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.producto import Producto
