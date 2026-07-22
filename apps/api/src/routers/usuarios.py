from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.deps import require_admin
from src.models.usuario import Usuario
from src.schemas.base import PaginatedResponse
from src.schemas.usuario import UsuarioCambiarEstadoRequest, UsuarioResponse
from src.services.usuarios import UsuariosService

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


def _ip_origen(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PaginatedResponse[UsuarioResponse])
async def listar_usuarios(
    rol: str | None = None,
    activo: bool | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UsuarioResponse]:
    service = UsuariosService(session)
    usuarios, total = await service.listar(rol, activo, search, page, limit)
    return PaginatedResponse[UsuarioResponse](
        data=[UsuarioResponse.model_validate(u) for u in usuarios],
        total=total,
        page=page,
        limit=limit,
    )


@router.patch("/{id}/estado", response_model=UsuarioResponse)
async def cambiar_estado_usuario(
    id: UUID,
    body: UsuarioCambiarEstadoRequest,
    request: Request,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    service = UsuariosService(session)
    usuario = await service.cambiar_estado(
        id, body.activo, current_user, _ip_origen(request)
    )
    return UsuarioResponse.model_validate(usuario)
