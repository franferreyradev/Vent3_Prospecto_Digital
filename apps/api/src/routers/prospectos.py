from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.deps import require_admin
from src.models.usuario import Usuario
from src.schemas.prospecto import (
    ProspectoActivarResponse,
    ProspectoCreateRequest,
    ProspectoResponse,
)
from src.services.prospectos import ProspectosService

router = APIRouter(prefix="/api/prospectos", tags=["prospectos"])


class ProspectoActivarRequest(BaseModel):
    producto_id: UUID


def _ip_origen(request: Request) -> str | None:
    return request.client.host if request.client else None


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
