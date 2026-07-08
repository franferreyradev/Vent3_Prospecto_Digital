from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.deps import require_admin
from src.models.usuario import Usuario
from src.schemas.base import PaginatedResponse
from src.schemas.prospecto import (
    ProspectoActivarResponse,
    ProspectoCreateRequest,
    ProspectoDownloadUrlResponse,
    ProspectoResponse,
)
from src.services.prospectos import ProspectosService

router = APIRouter(prefix="/api/prospectos", tags=["prospectos"])


class ProspectoActivarRequest(BaseModel):
    producto_id: UUID


def _ip_origen(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PaginatedResponse[ProspectoResponse])
async def listar_prospectos(
    producto_id: UUID | None = None,
    estado_vigencia: Literal["en_revision", "vigente", "reemplazado"] | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ProspectoResponse]:
    service = ProspectosService(session)
    prospectos, total = await service.listar(producto_id, estado_vigencia, page, limit)
    return PaginatedResponse[ProspectoResponse](
        data=[ProspectoResponse.model_validate(p) for p in prospectos],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{id}/download-url", response_model=ProspectoDownloadUrlResponse)
async def obtener_download_url(
    id: UUID,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProspectoDownloadUrlResponse:
    service = ProspectosService(session)
    url = await service.obtener_url_descarga(id)
    return ProspectoDownloadUrlResponse(url=url)


@router.post("", response_model=ProspectoResponse, status_code=201)
async def subir_prospecto(
    request: Request,
    numero_expediente: str = Form(...),
    version: int = Form(...),
    tipo_audiencia: Literal["publico_general", "profesional_salud", "unico"] = Form(...),
    producto_id: UUID = Form(...),
    archivo: UploadFile = File(...),
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProspectoResponse:
    datos = ProspectoCreateRequest(
        numero_expediente=numero_expediente,
        version=version,
        tipo_audiencia=tipo_audiencia,
        producto_id=producto_id,
    )
    service = ProspectosService(session)
    prospecto = await service.subir(datos, archivo, current_user.id, _ip_origen(request))
    return ProspectoResponse.model_validate(prospecto)


@router.patch("/{id}/activar", response_model=ProspectoActivarResponse)
async def activar_prospecto(
    id: UUID,
    body: ProspectoActivarRequest,
    request: Request,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProspectoActivarResponse:
    service = ProspectosService(session)
    resultado = await service.activar(id, body.producto_id, current_user.id, _ip_origen(request))
    return ProspectoActivarResponse(
        activado=ProspectoResponse.model_validate(resultado["activado"]),
        reemplazado=(
            ProspectoResponse.model_validate(resultado["reemplazado"])
            if resultado["reemplazado"]
            else None
        ),
    )
