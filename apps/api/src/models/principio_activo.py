from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base


class PrincipioActivo(Base):
    __tablename__ = "principios_activos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    # nombre_normalizado es generado por trg_normalizar_principio_activo — solo lectura
    nombre_normalizado: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    productos_asociados: Mapped[list[ProductoPrincipio]] = relationship(
        "ProductoPrincipio", back_populates="principio"
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.producto_principio import ProductoPrincipio
