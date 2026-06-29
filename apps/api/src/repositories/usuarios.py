from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.usuario import Usuario
from src.repositories.base import BaseRepository

LOCKOUT_MINUTOS = 15
MAX_INTENTOS = 5


class UsuariosRepository(BaseRepository[Usuario]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Usuario)

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.session.execute(
            select(Usuario).where(Usuario.email == email)
        )
        return result.scalar_one_or_none()

    async def registrar_intento_fallido(self, usuario: Usuario) -> Usuario:
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= MAX_INTENTOS:
            usuario.bloqueado_hasta = datetime.now(timezone.utc) + timedelta(
                minutes=LOCKOUT_MINUTOS
            )
        self.session.add(usuario)
        await self.session.flush()
        return usuario

    async def registrar_acceso_exitoso(self, usuario: Usuario) -> Usuario:
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.ultimo_acceso = datetime.now(timezone.utc)
        self.session.add(usuario)
        await self.session.flush()
        return usuario

    async def esta_bloqueado(self, usuario: Usuario) -> bool:
        if usuario.bloqueado_hasta is None:
            return False
        now = datetime.now(timezone.utc)
        # bloqueado_hasta puede ser naive o aware según asyncpg
        bloqueado_hasta = usuario.bloqueado_hasta
        if bloqueado_hasta.tzinfo is None:
            bloqueado_hasta = bloqueado_hasta.replace(tzinfo=timezone.utc)
        return bloqueado_hasta > now
