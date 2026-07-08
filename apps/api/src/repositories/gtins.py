from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gtin_registro import GtinRegistro
from src.repositories.base import BaseRepository


class GtinsRepository(BaseRepository[GtinRegistro]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GtinRegistro)
