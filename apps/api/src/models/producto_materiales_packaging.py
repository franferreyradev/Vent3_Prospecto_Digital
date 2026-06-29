from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base
from src.models.enums import tipo_envase_enum


class ProductoMaterialesPackaging(Base):
    __tablename__ = "producto_materiales_packaging"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    tipo_envase: Mapped[str] = mapped_column(tipo_envase_enum, nullable=False)
    codigo_estuche: Mapped[str | None] = mapped_column(String(30), nullable=True)
    codigo_aluminio: Mapped[str | None] = mapped_column(String(30), nullable=True)
    codigo_pvc: Mapped[str | None] = mapped_column(String(30), nullable=True)
    codigo_frasco: Mapped[str | None] = mapped_column(String(30), nullable=True)
    codigo_etiqueta: Mapped[str | None] = mapped_column(String(30), nullable=True)
    codigo_vaso_inserto: Mapped[str | None] = mapped_column(String(30), nullable=True)
    codigo_tapa: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    # Sin onupdate= — el trigger trg_updated_at_producto_materiales_packaging lo gestiona
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    producto: Mapped[Producto] = relationship(
        "Producto", back_populates="materiales_packaging"
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.producto import Producto
