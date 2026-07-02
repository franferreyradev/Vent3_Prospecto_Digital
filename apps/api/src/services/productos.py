from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.producto import Producto
from src.repositories.productos import ProductosRepository
from src.schemas.producto import ProductoUpdateRequest
from src.services.auditoria import AuditoriaService


class ProductosService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductosRepository(session)
        self.auditoria = AuditoriaService(session)

    async def listar(
        self,
        estado: str | None,
        canal: str | None,
        search: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[Producto], int]:
        offset = (page - 1) * limit
        return await self.repo.get_all_filtrado(
            estado=estado, canal=canal, search=search, offset=offset, limit=limit
        )

    async def obtener_detalle(self, id: UUID) -> Producto:
        producto = await self.repo.get_detalle_completo(id)
        if producto is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return producto

    async def actualizar(
        self,
        id: UUID,
        datos: ProductoUpdateRequest,
        usuario_id: UUID,
        ip_origen: str | None,
    ) -> Producto:
        producto = await self.repo.get_detalle_completo(id)
        if producto is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        campos_modificados = datos.model_dump(exclude_none=True)

        for campo, valor_nuevo in campos_modificados.items():
            valor_anterior = getattr(producto, campo)
            setattr(producto, campo, valor_nuevo)
            await self.auditoria.registrar_cambio(
                tabla="productos",
                registro_id=producto.id,
                accion="UPDATE",
                usuario_id=usuario_id,
                campo=campo,
                valor_anterior=valor_anterior,
                valor_nuevo=valor_nuevo,
                ip_origen=ip_origen,
            )

        self.session.add(producto)
        await self.session.flush()
        await self.session.refresh(producto, attribute_names=["updated_at"])
        return producto

    async def cambiar_estado(
        self,
        id: UUID,
        nuevo_estado: str,
        usuario_id: UUID,
        ip_origen: str | None,
    ) -> Producto:
        producto = await self.repo.get_detalle_completo(id)
        if producto is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if producto.estado == nuevo_estado:
            return producto

        estado_anterior = producto.estado
        await self.repo.cambiar_estado(producto, nuevo_estado)
        await self.auditoria.registrar_cambio_estado_producto(
            producto_id=producto.id,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            usuario_id=usuario_id,
            ip_origen=ip_origen,
        )
        await self.session.refresh(producto, attribute_names=["updated_at"])
        return producto
