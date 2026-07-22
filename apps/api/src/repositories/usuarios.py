from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
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

    async def get_filtrado(
        self,
        rol: str | None = None,
        activo: bool | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Usuario], int]:
        query = select(Usuario)
        count_query = select(func.count()).select_from(Usuario)

        if rol:
            query = query.where(Usuario.rol == rol)
            count_query = count_query.where(Usuario.rol == rol)
        if activo is not None:
            query = query.where(Usuario.activo == activo)
            count_query = count_query.where(Usuario.activo == activo)
        if search:
            filtro_busqueda = or_(
                Usuario.email.ilike(f"%{search}%"),
                Usuario.nombre.ilike(f"%{search}%"),
            )
            query = query.where(filtro_busqueda)
            count_query = count_query.where(filtro_busqueda)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            query.order_by(Usuario.created_at.desc()).offset(offset).limit(limit)
        )
        usuarios = list(result.scalars().all())

        return usuarios, total
