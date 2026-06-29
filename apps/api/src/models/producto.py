from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base
from src.models.enums import canal_enum, estado_producto_enum


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    codigo_interno: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    nombre_comercial: Mapped[str] = mapped_column(String(200), nullable=False)
    forma_farmaceutica: Mapped[str] = mapped_column(String(100), nullable=False)
    presentacion_cantidad: Mapped[str] = mapped_column(String(50), nullable=False)
    canal: Mapped[str] = mapped_column(canal_enum, nullable=False, default="farmacia")
    estado: Mapped[str] = mapped_column(estado_producto_enum, nullable=False, default="activo")
    tiene_prospecto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    # Sin onupdate= — el trigger trg_updated_at_productos lo gestiona
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    principios: Mapped[list[ProductoPrincipio]] = relationship(
        "ProductoPrincipio", back_populates="producto", cascade="all, delete-orphan"
    )
    prospectos_asociados: Mapped[list[ProductoProspecto]] = relationship(
        "ProductoProspecto", back_populates="producto"
    )
    gtin_registros: Mapped[list[GtinRegistro]] = relationship(
        "GtinRegistro", back_populates="producto"
    )
    materiales_packaging: Mapped[ProductoMaterialesPackaging | None] = relationship(
        "ProductoMaterialesPackaging", back_populates="producto", uselist=False
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.producto_principio import ProductoPrincipio
    from src.models.producto_prospecto import ProductoProspecto
    from src.models.gtin_registro import GtinRegistro
    from src.models.producto_materiales_packaging import ProductoMaterialesPackaging
