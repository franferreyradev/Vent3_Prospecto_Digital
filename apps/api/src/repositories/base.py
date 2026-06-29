from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: UUID) -> T | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(self, offset: int = 0, limit: int = 50) -> list[T]:
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model)  # type: ignore[arg-type]
        )
        return result.scalar_one()

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        return obj
