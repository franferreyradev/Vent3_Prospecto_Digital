from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.deps import require_admin
from src.models.usuario import Usuario
from src.schemas.audit import AuditLogResponse
from src.schemas.base import PaginatedResponse
from src.services.audit import AuditService

router = APIRouter(prefix="/api/audit-log", tags=["audit"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def listar_audit_log(
    tabla: str | None = None,
    registro_id: UUID | None = None,
    usuario_id: UUID | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AuditLogResponse]:
    service = AuditService(session)
    logs, total = await service.listar(tabla, registro_id, usuario_id, desde, hasta, page, limit)
    return PaginatedResponse[AuditLogResponse](
        data=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        limit=limit,
    )
