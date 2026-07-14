from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gtin_registro import GtinRegistro
from src.repositories.base import BaseRepository


class GtinsRepository(BaseRepository[GtinRegistro]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GtinRegistro)

    async def get_vigente_por_producto(
        self, producto_id: UUID, excluir_id: UUID
    ) -> GtinRegistro | None:
        result = await self.session.execute(
            select(GtinRegistro).where(
                GtinRegistro.producto_id == producto_id,
                GtinRegistro.es_vigente == True,  # noqa: E712
                GtinRegistro.id != excluir_id,
            )
        )
        return result.scalar_one_or_none()
