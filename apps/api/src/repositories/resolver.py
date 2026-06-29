from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.gtin_registro import GtinRegistro
from src.models.producto import Producto
from src.models.producto_prospecto import ProductoProspecto
from src.models.prospecto import Prospecto


class ResolverRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolver_gtin(self, gtin: str) -> dict:
        # 1. Buscar GTIN vigente
        gtin_result = await self.session.execute(
            select(GtinRegistro)
            .where(GtinRegistro.gtin == gtin, GtinRegistro.es_vigente == True)  # noqa: E712
            .options(selectinload(GtinRegistro.producto))
        )
        gtin_reg = gtin_result.scalar_one_or_none()

        if gtin_reg is None:
            return {"error": "no_encontrado"}

        # 2. Verificar estado del producto
        producto = gtin_reg.producto
        if producto.estado == "inactivo":
            return {"error": "inactivo"}

        # 3. Buscar prospectos vigentes del producto
        prospectos_result = await self.session.execute(
            select(Prospecto)
            .join(ProductoProspecto, ProductoProspecto.prospecto_id == Prospecto.id)
            .where(
                ProductoProspecto.producto_id == producto.id,
                ProductoProspecto.activo == True,  # noqa: E712
                Prospecto.estado_vigencia == "vigente",
            )
        )
        prospectos = list(prospectos_result.scalars().all())

        if not prospectos:
            return {"error": "sin_prospecto"}

        return {"producto": producto, "prospectos": prospectos}
