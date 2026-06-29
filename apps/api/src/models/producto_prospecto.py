from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base


class ProductoProspecto(Base):
    __tablename__ = "producto_prospectos"
    # El índice único parcial (producto_id, prospecto_id WHERE activo=TRUE)
    # existe en la DB (migración 002). No se puede expresar como índice parcial
    # en __table_args__ de SQLAlchemy sin Index(..., postgresql_where=...) — se confía
    # en el constraint de DB.

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    prospecto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prospectos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    variante_gs1: Mapped[str | None] = mapped_column(String(30), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    producto: Mapped[Producto] = relationship("Producto", back_populates="prospectos_asociados")
    prospecto: Mapped[Prospecto] = relationship("Prospecto", back_populates="productos_asociados")


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.producto import Producto
    from src.models.prospecto import Prospecto
