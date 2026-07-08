from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.producto import Producto
from src.models.producto_prospecto import ProductoProspecto
from src.models.prospecto import Prospecto
from src.repositories.base import BaseRepository


class ProspectosRepository(BaseRepository[Prospecto]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Prospecto)

    async def listar(
        self,
        producto_id: UUID | None,
        estado_vigencia: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Prospecto], int]:
        query = select(Prospecto)
        count_query = select(func.count()).select_from(Prospecto)

        if producto_id is not None:
            query = query.join(
                ProductoProspecto, ProductoProspecto.prospecto_id == Prospecto.id
            ).where(ProductoProspecto.producto_id == producto_id)
            count_query = count_query.join(
                ProductoProspecto, ProductoProspecto.prospecto_id == Prospecto.id
            ).where(ProductoProspecto.producto_id == producto_id)

        if estado_vigencia is not None:
            query = query.where(Prospecto.estado_vigencia == estado_vigencia)
            count_query = count_query.where(Prospecto.estado_vigencia == estado_vigencia)

        query = query.order_by(Prospecto.created_at.desc()).offset(offset).limit(limit)

        total = (await self.session.execute(count_query)).scalar_one()
        prospectos = list((await self.session.execute(query)).scalars().all())
        return prospectos, total

    async def get_vigente_por_producto_y_audiencia(
        self, producto_id: UUID, tipo_audiencia: str
    ) -> Prospecto | None:
        result = await self.session.execute(
            select(Prospecto)
            .join(ProductoProspecto, ProductoProspecto.prospecto_id == Prospecto.id)
            .where(
                ProductoProspecto.producto_id == producto_id,
                ProductoProspecto.activo == True,  # noqa: E712
                Prospecto.tipo_audiencia == tipo_audiencia,
                Prospecto.estado_vigencia == "vigente",
            )
        )
        return result.scalar_one_or_none()

    async def get_todos_por_producto(self, producto_id: UUID) -> list[ProductoProspecto]:
        result = await self.session.execute(
            select(ProductoProspecto).where(ProductoProspecto.producto_id == producto_id)
        )
        return list(result.scalars().all())

    async def activar_prospecto(
        self, producto_id: UUID, prospecto_id: UUID, tipo_audiencia: str
    ) -> dict:
        # 1. Buscar el prospecto activo anterior (misma audiencia)
        anterior_result = await self.session.execute(
            select(ProductoProspecto)
            .join(Prospecto, Prospecto.id == ProductoProspecto.prospecto_id)
            .where(
                ProductoProspecto.producto_id == producto_id,
                ProductoProspecto.activo == True,  # noqa: E712
                Prospecto.tipo_audiencia == tipo_audiencia,
            )
        )
        asociacion_anterior = anterior_result.scalar_one_or_none()
        prospecto_anterior: Prospecto | None = None

        if asociacion_anterior:
            # 2. Reemplazar el anterior
            prospecto_anterior_result = await self.session.execute(
                select(Prospecto).where(Prospecto.id == asociacion_anterior.prospecto_id)
            )
            prospecto_anterior = prospecto_anterior_result.scalar_one_or_none()
            if prospecto_anterior:
                prospecto_anterior.estado_vigencia = "reemplazado"
                self.session.add(prospecto_anterior)
            asociacion_anterior.activo = False
            self.session.add(asociacion_anterior)

        # 3. Nueva asociación activa
        nueva_asociacion = ProductoProspecto(
            producto_id=producto_id,
            prospecto_id=prospecto_id,
            activo=True,
        )
        self.session.add(nueva_asociacion)

        # 4. Prospecto nuevo → vigente
        nuevo_result = await self.session.execute(
            select(Prospecto).where(Prospecto.id == prospecto_id)
        )
        prospecto_nuevo = nuevo_result.scalar_one()
        prospecto_nuevo.estado_vigencia = "vigente"
        self.session.add(prospecto_nuevo)

        # 5. Producto → tiene_prospecto = True
        producto_result = await self.session.execute(
            select(Producto).where(Producto.id == producto_id)
        )
        producto = producto_result.scalar_one()
        producto.tiene_prospecto = True
        self.session.add(producto)

        await self.session.flush()

        return {"activado": prospecto_nuevo, "reemplazado": prospecto_anterior}
