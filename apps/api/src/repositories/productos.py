from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.models.producto import Producto
from src.models.producto_principio import ProductoPrincipio
from src.repositories.base import BaseRepository


class ProductosRepository(BaseRepository[Producto]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Producto)

    async def get_by_codigo_interno(self, codigo: str) -> Producto | None:
        result = await self.session.execute(
            select(Producto).where(Producto.codigo_interno == codigo)
        )
        return result.scalar_one_or_none()

    async def get_all_filtrado(
        self,
        estado: str | None = None,
        canal: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Producto], int]:
        query = select(Producto)
        count_query = select(func.count()).select_from(Producto)

        if estado:
            query = query.where(Producto.estado == estado)
            count_query = count_query.where(Producto.estado == estado)
        if canal:
            query = query.where(Producto.canal == canal)
            count_query = count_query.where(Producto.canal == canal)
        if search:
            like = f"%{search}%"
            condition = or_(
                Producto.nombre_comercial.ilike(like),
                Producto.codigo_interno.ilike(like),
            )
            query = query.where(condition)
            count_query = count_query.where(condition)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(query.offset(offset).limit(limit))
        productos = list(result.scalars().all())

        return productos, total

    async def get_detalle_completo(self, id: UUID) -> Producto | None:
        result = await self.session.execute(
            select(Producto)
            .where(Producto.id == id)
            .options(
                selectinload(Producto.principios).selectinload(ProductoPrincipio.principio),
                selectinload(Producto.gtin_registros),
                selectinload(Producto.prospectos_asociados),
                joinedload(Producto.materiales_packaging),
            )
        )
        return result.scalar_one_or_none()

    async def cambiar_estado(self, producto: Producto, nuevo_estado: str) -> Producto:
        producto.estado = nuevo_estado
        self.session.add(producto)
        await self.session.flush()
        return producto
