from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.deps import require_admin
from src.models.usuario import Usuario
from src.schemas.gtin import GtinRegistroResponse, GtinUpdateRequest
from src.services.gtins import GtinsService

router = APIRouter(prefix="/api/gtins", tags=["gtins"])


def _ip_origen(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.patch("/{id}", response_model=GtinRegistroResponse)
async def actualizar_gtin(
    id: UUID,
    body: GtinUpdateRequest,
    request: Request,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> GtinRegistroResponse:
    service = GtinsService(session)
    gtin_registro = await service.actualizar(id, body, current_user.id, _ip_origen(request))
    return GtinRegistroResponse.model_validate(gtin_registro)
