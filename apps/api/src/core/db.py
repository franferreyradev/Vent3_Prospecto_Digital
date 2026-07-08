from collections.abc import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except HTTPException:
            # Un HTTPException es una respuesta de aplicación esperada (401,
            # 404, 422, etc.), no un error de integridad transaccional. Los
            # cambios de estado hechos antes de levantarla (ej. contador de
            # intentos fallidos de login) deben persistir igual.
            await session.commit()
            raise
        except Exception:
            await session.rollback()
            raise
