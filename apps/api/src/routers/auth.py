import asyncio

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import get_db
from src.core.deps import get_current_user
from src.core.security import (
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    crear_access_token,
    verificar_password,
)
from src.models.usuario import Usuario
from src.repositories.usuarios import UsuariosRepository
from src.schemas.usuario import LoginRequest, UsuarioResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

_COOKIE_SECURE = settings.ENVIRONMENT == "production"


@router.post("/login", status_code=204)
async def login(
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> None:
    repo = UsuariosRepository(session)

    usuario = await repo.get_by_email(body.email)
    if usuario is None:
        await asyncio.sleep(0.3)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if await repo.esta_bloqueado(usuario):
        raise HTTPException(
            status_code=401,
            detail="Cuenta bloqueada temporalmente. Intentar en 15 minutos.",
        )

    if not verificar_password(body.password, usuario.password_hash):
        await repo.registrar_intento_fallido(usuario)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    await repo.registrar_acceso_exitoso(usuario)
    token = crear_access_token({"sub": usuario.email})

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.get("/me", response_model=UsuarioResponse)
async def me(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    return current_user
