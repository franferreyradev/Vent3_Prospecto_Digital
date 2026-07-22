from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    INVITACION_EXPIRE_HOURS,
    crear_password_hash,
    generar_token_invitacion,
    hash_token,
)
from src.models.invitacion_usuario import InvitacionUsuario
from src.models.usuario import Usuario
from src.repositories.invitaciones import InvitacionesRepository
from src.repositories.usuarios import UsuariosRepository
from src.schemas.invitacion import InvitacionCreateRequest
from src.services.auditoria import AuditoriaService

MENSAJE_TOKEN_INVALIDO = "Invitación inválida o expirada"


def _esta_vigente(invitacion: InvitacionUsuario) -> bool:
    if invitacion.usado_en is not None:
        return False
    expira_en = invitacion.expira_en
    if expira_en.tzinfo is None:
        expira_en = expira_en.replace(tzinfo=timezone.utc)
    return expira_en > datetime.now(timezone.utc)


def calcular_estado(invitacion: InvitacionUsuario) -> str:
    if invitacion.usado_en is not None:
        return "usada"
    if _esta_vigente(invitacion):
        return "pendiente"
    return "expirada"


class InvitacionesService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InvitacionesRepository(session)
        self.usuarios_repo = UsuariosRepository(session)
        self.auditoria = AuditoriaService(session)

    async def crear(
        self,
        datos: InvitacionCreateRequest,
        usuario_admin: Usuario,
        ip_origen: str | None,
    ) -> tuple[InvitacionUsuario, str]:
        usuario_existente = await self.usuarios_repo.get_by_email(datos.email)
        if usuario_existente is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya existe un usuario con ese email",
            )

        token_plano = generar_token_invitacion()
        invitacion = InvitacionUsuario(
            email=datos.email,
            nombre=datos.nombre,
            rol=datos.rol,
            token_hash=hash_token(token_plano),
            creado_por=usuario_admin.id,
            expira_en=datetime.now(timezone.utc)
            + timedelta(hours=INVITACION_EXPIRE_HOURS),
        )
        await self.repo.create(invitacion)

        await self.auditoria.registrar_cambio(
            tabla="invitaciones_usuario",
            registro_id=invitacion.id,
            accion="INSERT",
            usuario_id=usuario_admin.id,
            campo="email",
            valor_nuevo=f"{datos.email} ({datos.rol})",
            ip_origen=ip_origen,
        )

        return invitacion, token_plano

    async def validar(self, token_plano: str) -> InvitacionUsuario:
        invitacion = await self.repo.get_by_token_hash(hash_token(token_plano))
        if invitacion is None or not _esta_vigente(invitacion):
            raise HTTPException(status_code=404, detail=MENSAJE_TOKEN_INVALIDO)
        return invitacion

    async def activar(
        self,
        token_plano: str,
        password: str,
        ip_origen: str | None,
    ) -> Usuario:
        invitacion = await self.validar(token_plano)

        usuario_existente = await self.usuarios_repo.get_by_email(invitacion.email)
        if usuario_existente is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya existe un usuario con ese email",
            )

        nuevo_usuario = Usuario(
            email=invitacion.email,
            nombre=invitacion.nombre,
            password_hash=crear_password_hash(password),
            rol=invitacion.rol,
        )

        try:
            await self.usuarios_repo.create(nuevo_usuario)
        except IntegrityError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Ya existe un usuario con ese email",
            ) from e

        invitacion.usado_en = datetime.now(timezone.utc)
        invitacion.usuario_creado_id = nuevo_usuario.id
        await self.repo.update(invitacion)

        await self.auditoria.registrar_cambio(
            tabla="usuarios",
            registro_id=nuevo_usuario.id,
            accion="INSERT",
            usuario_id=nuevo_usuario.id,
            campo="rol",
            valor_nuevo=nuevo_usuario.rol,
            ip_origen=ip_origen,
        )

        return nuevo_usuario

    async def listar(
        self,
        estado: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[InvitacionUsuario], int]:
        offset = (page - 1) * limit
        return await self.repo.get_filtrado(estado=estado, offset=offset, limit=limit)
