from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import COOKIE_NAME, decodificar_token
from src.models.usuario import Usuario
from src.repositories.usuarios import UsuariosRepository


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decodificar_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Sesión expirada")

    email: str | None = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Sesión expirada")

    repo = UsuariosRepository(session)
    usuario = await repo.get_by_email(email)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    return usuario


async def require_admin(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return current_user
