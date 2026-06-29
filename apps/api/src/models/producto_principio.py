from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class ProductoPrincipio(Base):
    __tablename__ = "producto_principios"
    __table_args__ = (UniqueConstraint("producto_id", "principio_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    principio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("principios_activos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    potencia: Mapped[str] = mapped_column(String(30), nullable=False)
    unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # Relaciones
    producto: Mapped[Producto] = relationship("Producto", back_populates="principios")
    principio: Mapped[PrincipioActivo] = relationship(
        "PrincipioActivo", back_populates="productos_asociados"
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.producto import Producto
    from src.models.principio_activo import PrincipioActivo
