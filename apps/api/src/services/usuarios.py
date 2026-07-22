from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.usuario import Usuario
from src.repositories.usuarios import UsuariosRepository
from src.services.auditoria import AuditoriaService


class UsuariosService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UsuariosRepository(session)
        self.auditoria = AuditoriaService(session)

    async def listar(
        self,
        rol: str | None,
        activo: bool | None,
        search: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[Usuario], int]:
        offset = (page - 1) * limit
        return await self.repo.get_filtrado(
            rol=rol, activo=activo, search=search, offset=offset, limit=limit
        )

    async def cambiar_estado(
        self,
        id: UUID,
        activo: bool,
        usuario_admin: Usuario,
        ip_origen: str | None,
    ) -> Usuario:
        usuario = await self.repo.get_by_id(id)
        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if usuario.id == usuario_admin.id and not activo:
            raise HTTPException(
                status_code=409,
                detail="No podés desactivar tu propia cuenta",
            )

        valor_anterior = usuario.activo
        usuario.activo = activo
        await self.repo.update(usuario)

        await self.auditoria.registrar_cambio(
            tabla="usuarios",
            registro_id=usuario.id,
            accion="UPDATE",
            usuario_id=usuario_admin.id,
            campo="activo",
            valor_anterior=valor_anterior,
            valor_nuevo=activo,
            ip_origen=ip_origen,
        )

        return usuario
