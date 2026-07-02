from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog
from src.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditRepository(session)

    async def listar(
        self,
        tabla: str | None,
        registro_id: UUID | None,
        usuario_id: UUID | None,
        desde: datetime | None,
        hasta: datetime | None,
        page: int,
        limit: int,
    ) -> tuple[list[AuditLog], int]:
        offset = (page - 1) * limit
        return await self.repo.get_filtrado(
            tabla=tabla,
            registro_id=registro_id,
            usuario_id=usuario_id,
            desde=desde,
            hasta=hasta,
            offset=offset,
            limit=limit,
        )
