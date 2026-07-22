from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.invitacion_usuario import InvitacionUsuario
from src.repositories.base import BaseRepository


class InvitacionesRepository(BaseRepository[InvitacionUsuario]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, InvitacionUsuario)

    async def get_by_token_hash(self, token_hash: str) -> InvitacionUsuario | None:
        result = await self.session.execute(
            select(InvitacionUsuario).where(InvitacionUsuario.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_filtrado(
        self,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[InvitacionUsuario], int]:
        query = select(InvitacionUsuario)
        count_query = select(func.count()).select_from(InvitacionUsuario)
        now = datetime.now(timezone.utc)

        if estado == "pendiente":
            filtro = (InvitacionUsuario.usado_en.is_(None)) & (
                InvitacionUsuario.expira_en > now
            )
        elif estado == "usada":
            filtro = InvitacionUsuario.usado_en.is_not(None)
        elif estado == "expirada":
            filtro = (InvitacionUsuario.usado_en.is_(None)) & (
                InvitacionUsuario.expira_en <= now
            )
        else:
            filtro = None

        if filtro is not None:
            query = query.where(filtro)
            count_query = count_query.where(filtro)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            query.order_by(InvitacionUsuario.creado_en.desc()).offset(offset).limit(limit)
        )
        invitaciones = list(result.scalars().all())

        return invitaciones, total
