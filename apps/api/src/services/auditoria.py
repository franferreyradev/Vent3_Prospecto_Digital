import logging
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.audit import AuditRepository

logger = logging.getLogger(__name__)


class AuditoriaService:
    # Patrón de uso desde un router handler:
    #   auditoria = AuditoriaService(session)
    #   await auditoria.registrar_cambio(
    #       tabla='productos', registro_id=producto.id, accion='UPDATE',
    #       usuario_id=current_user.id, campo='estado',
    #       valor_anterior=estado_anterior, valor_nuevo=nuevo_estado,
    #       ip_origen=request.client.host if request.client else None,
    #   )

    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditRepository(session)

    async def registrar_cambio(
        self,
        tabla: str,
        registro_id: UUID,
        accion: Literal["INSERT", "UPDATE", "DELETE"],
        usuario_id: UUID,
        campo: str | None = None,
        valor_anterior: Any | None = None,
        valor_nuevo: Any | None = None,
        ip_origen: str | None = None,
    ) -> None:
        try:
            await self.repo.registrar(
                tabla_afectada=tabla,
                registro_id=registro_id,
                accion=accion,
                usuario_id=usuario_id,
                campo_modificado=campo,
                valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
                valor_nuevo=str(valor_nuevo) if valor_nuevo is not None else None,
                ip_origen=ip_origen,
            )
        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}")

    async def registrar_activacion_prospecto(
        self,
        prospecto_id: UUID,
        usuario_id: UUID,
        estado_anterior: str,
        ip_origen: str | None = None,
    ) -> None:
        await self.registrar_cambio(
            tabla="prospectos",
            registro_id=prospecto_id,
            accion="UPDATE",
            usuario_id=usuario_id,
            campo="estado_vigencia",
            valor_anterior=estado_anterior,
            valor_nuevo="vigente",
            ip_origen=ip_origen,
        )

    async def registrar_reemplazo_prospecto(
        self,
        prospecto_id: UUID,
        usuario_id: UUID,
        ip_origen: str | None = None,
    ) -> None:
        await self.registrar_cambio(
            tabla="prospectos",
            registro_id=prospecto_id,
            accion="UPDATE",
            usuario_id=usuario_id,
            campo="estado_vigencia",
            valor_anterior="vigente",
            valor_nuevo="reemplazado",
            ip_origen=ip_origen,
        )

    async def registrar_cambio_estado_producto(
        self,
        producto_id: UUID,
        estado_anterior: str,
        estado_nuevo: str,
        usuario_id: UUID,
        ip_origen: str | None = None,
    ) -> None:
        await self.registrar_cambio(
            tabla="productos",
            registro_id=producto_id,
            accion="UPDATE",
            usuario_id=usuario_id,
            campo="estado",
            valor_anterior=estado_anterior,
            valor_nuevo=estado_nuevo,
            ip_origen=ip_origen,
        )
