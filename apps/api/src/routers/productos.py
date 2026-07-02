from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.deps import require_admin
from src.models.producto import Producto
from src.models.usuario import Usuario
from src.schemas.base import PaginatedResponse
from src.schemas.producto import (
    PrincipioActivoEnProducto,
    ProductoCambiarEstadoRequest,
    ProductoDetalleResponse,
    ProductoListResponse,
    ProductoUpdateRequest,
)
from src.services.productos import ProductosService

router = APIRouter(prefix="/api/productos", tags=["productos"])


def _to_detalle_response(producto: Producto) -> ProductoDetalleResponse:
    principios = [
        PrincipioActivoEnProducto(
            id=pp.id,
            nombre=pp.principio.nombre,
            potencia=pp.potencia,
            unidad=pp.unidad,
            orden=pp.orden,
        )
        for pp in producto.principios
    ]
    return ProductoDetalleResponse(
        id=producto.id,
        codigo_interno=producto.codigo_interno,
        nombre_comercial=producto.nombre_comercial,
        forma_farmaceutica=producto.forma_farmaceutica,
        presentacion_cantidad=producto.presentacion_cantidad,
        canal=producto.canal,
        estado=producto.estado,
        tiene_prospecto=producto.tiene_prospecto,
        principios=principios,
        created_at=producto.created_at,
        updated_at=producto.updated_at,
    )


def _ip_origen(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PaginatedResponse[ProductoListResponse])
async def listar_productos(
    estado: str | None = None,
    canal: str | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ProductoListResponse]:
    service = ProductosService(session)
    productos, total = await service.listar(estado, canal, search, page, limit)
    return PaginatedResponse[ProductoListResponse](
        data=[ProductoListResponse.model_validate(p) for p in productos],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{id}", response_model=ProductoDetalleResponse)
async def obtener_producto(
    id: UUID,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProductoDetalleResponse:
    service = ProductosService(session)
    producto = await service.obtener_detalle(id)
    return _to_detalle_response(producto)


@router.patch("/{id}", response_model=ProductoDetalleResponse)
async def actualizar_producto(
    id: UUID,
    body: ProductoUpdateRequest,
    request: Request,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProductoDetalleResponse:
    service = ProductosService(session)
    producto = await service.actualizar(id, body, current_user.id, _ip_origen(request))
    return _to_detalle_response(producto)


@router.patch("/{id}/estado", response_model=ProductoDetalleResponse)
async def cambiar_estado_producto(
    id: UUID,
    body: ProductoCambiarEstadoRequest,
    request: Request,
    current_user: Usuario = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProductoDetalleResponse:
    service = ProductosService(session)
    producto = await service.cambiar_estado(id, body.estado, current_user.id, _ip_origen(request))
    return _to_detalle_response(producto)
