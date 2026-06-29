from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def registrar(
        self,
        tabla_afectada: str,
        registro_id: UUID,
        accion: str,
        usuario_id: UUID,
        campo_modificado: str | None = None,
        valor_anterior: str | None = None,
        valor_nuevo: str | None = None,
        ip_origen: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            accion=accion,
            usuario_id=usuario_id,
            campo_modificado=campo_modificado,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            ip_origen=ip_origen,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_filtrado(
        self,
        tabla: str | None = None,
        registro_id: UUID | None = None,
        usuario_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        if tabla:
            query = query.where(AuditLog.tabla_afectada == tabla)
            count_query = count_query.where(AuditLog.tabla_afectada == tabla)
        if registro_id:
            query = query.where(AuditLog.registro_id == registro_id)
            count_query = count_query.where(AuditLog.registro_id == registro_id)
        if usuario_id:
            query = query.where(AuditLog.usuario_id == usuario_id)
            count_query = count_query.where(AuditLog.usuario_id == usuario_id)
        if desde:
            query = query.where(AuditLog.created_at >= desde)
            count_query = count_query.where(AuditLog.created_at >= desde)
        if hasta:
            query = query.where(AuditLog.created_at <= hasta)
            count_query = count_query.where(AuditLog.created_at <= hasta)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )
        logs = list(result.scalars().all())

        return logs, total
