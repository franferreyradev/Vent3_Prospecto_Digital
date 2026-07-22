from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import get_db
from src.core.deps import require_admin
from src.core.security import COOKIE_MAX_AGE, COOKIE_NAME, crear_access_token
from src.models.usuario import Usuario
from src.schemas.base import PaginatedResponse
from src.schemas.invitacion import (
    InvitacionActivarRequest,
    InvitacionCreadaResponse,
    InvitacionCreateRequest,
    InvitacionResponse,
    InvitacionValidarResponse,
)
from src.schemas.usuario import UsuarioResponse
from src.services.invitaciones import InvitacionesService, calcular_estado

router = APIRouter(prefix="/api/invitaciones", tags=["invitaciones"])

_COOKIE_SECURE = settings.ENVIRONMENT == "production"


def _ip_origen(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=InvitacionCreadaResponse)
async def crear_invitacion(
    body: InvitacionCreateRequest,
    request: Request,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> InvitacionCreadaResponse:
    service = InvitacionesService(session)
    invitacion, token_plano = await service.crear(body, current_user, _ip_origen(request))
    return InvitacionCreadaResponse(
        id=invitacion.id,
        email=invitacion.email,
        nombre=invitacion.nombre,
        rol=invitacion.rol,
        expira_en=invitacion.expira_en,
        link=f"{settings.FRONTEND_URL}/activar-invitacion/{token_plano}",
    )


@router.get("", response_model=PaginatedResponse[InvitacionResponse])
async def listar_invitaciones(
    estado: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[InvitacionResponse]:
    service = InvitacionesService(session)
    invitaciones, total = await service.listar(estado, page, limit)
    return PaginatedResponse[InvitacionResponse](
        data=[
            InvitacionResponse(
                id=i.id,
                email=i.email,
                nombre=i.nombre,
                rol=i.rol,
                creado_en=i.creado_en,
                expira_en=i.expira_en,
                usado_en=i.usado_en,
                estado=calcular_estado(i),
            )
            for i in invitaciones
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/validar/{token}", response_model=InvitacionValidarResponse)
async def validar_invitacion(
    token: str,
    session: AsyncSession = Depends(get_db),
) -> InvitacionValidarResponse:
    service = InvitacionesService(session)
    invitacion = await service.validar(token)
    return InvitacionValidarResponse(
        email=invitacion.email, nombre=invitacion.nombre, rol=invitacion.rol
    )


@router.post("/{token}/activar", response_model=UsuarioResponse)
async def activar_invitacion(
    token: str,
    body: InvitacionActivarRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    service = InvitacionesService(session)
    usuario = await service.activar(token, body.password, _ip_origen(request))

    access_token = crear_access_token({"sub": usuario.email})
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )

    return UsuarioResponse.model_validate(usuario)
