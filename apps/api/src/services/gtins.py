from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gtin_registro import GtinRegistro
from src.repositories.gtins import GtinsRepository
from src.schemas.gtin import GtinUpdateRequest
from src.services.auditoria import AuditoriaService


class GtinsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GtinsRepository(session)
        self.auditoria = AuditoriaService(session)

    async def actualizar(
        self,
        id: UUID,
        datos: GtinUpdateRequest,
        usuario_id: UUID,
        ip_origen: str | None,
    ) -> GtinRegistro:
        gtin_registro = await self.repo.get_by_id(id)
        if gtin_registro is None:
            raise HTTPException(status_code=404, detail="GTIN no encontrado")

        campos_modificados = datos.model_dump(exclude_none=True)

        for campo, valor_nuevo in campos_modificados.items():
            valor_anterior = getattr(gtin_registro, campo)
            setattr(gtin_registro, campo, valor_nuevo)
            await self.auditoria.registrar_cambio(
                tabla="gtin_registro",
                registro_id=gtin_registro.id,
                accion="UPDATE",
                usuario_id=usuario_id,
                campo=campo,
                valor_anterior=valor_anterior,
                valor_nuevo=valor_nuevo,
                ip_origen=ip_origen,
            )

        await self.repo.update(gtin_registro)
        return gtin_registro
