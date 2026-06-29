"""
Tests T7 — Verificación de autorización por rol (require_admin).

Patrón para proteger endpoints en T9+:
    from src.core.deps import require_admin
    @router.get("/ruta", response_model=AlgoResponse)
    async def mi_endpoint(
        current_user: Usuario = Depends(require_admin),
        session: AsyncSession = Depends(get_db)
    ):
        ...
"""

import os
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.db import get_db
from src.core.deps import require_admin
from src.core.security import ALGORITHM, COOKIE_NAME, crear_access_token
from src.models.usuario import Usuario

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")


# Provee conexiones frescas sin pooling — evita conflictos de event loop entre tests.
async def _get_db_nullpool() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


# App de prueba con un endpoint protegido por require_admin.
# Usa NullPool para que cada request cree su propia conexión.
_admin_app = FastAPI()
_admin_app.dependency_overrides[get_db] = _get_db_nullpool


@_admin_app.get("/test-protegido")
async def ruta_admin(user: Usuario = Depends(require_admin)):
    return {"rol": user.rol}


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_ok():
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL no configurada")
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        conn = await engine.connect()
        await conn.close()
    except Exception as e:
        pytest.skip(f"DB no accesible: {e}")
    finally:
        await engine.dispose()


# ── TC1: sin cookie → 401 ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_admin_sin_cookie_retorna_401() -> None:
    async with AsyncClient(transport=ASGITransport(app=_admin_app), base_url="http://test") as client:
        response = await client.get("/test-protegido")

    assert response.status_code == 401


# ── TC2: cookie de admin válida → 200 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_admin_con_cookie_valida_retorna_200(db_ok: None) -> None:
    if not ADMIN_EMAIL or not SECRET_KEY:
        pytest.skip("ADMIN_EMAIL o SECRET_KEY no configuradas")

    token = crear_access_token({"sub": ADMIN_EMAIL})

    async with AsyncClient(transport=ASGITransport(app=_admin_app), base_url="http://test") as client:
        client.cookies.set(COOKIE_NAME, token)
        response = await client.get("/test-protegido")

    assert response.status_code == 200
    assert response.json()["rol"] == "admin"


# ── TC3: JWT con clave incorrecta → 401 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_admin_jwt_key_incorrecta_retorna_401() -> None:
    token_invalido = jwt.encode(
        {
            "sub": "admin@vent3.test",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        },
        "clave-secreta-incorrecta-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        algorithm=ALGORITHM,
    )

    async with AsyncClient(transport=ASGITransport(app=_admin_app), base_url="http://test") as client:
        client.cookies.set(COOKIE_NAME, token_invalido)
        response = await client.get("/test-protegido")

    assert response.status_code == 401
    assert response.json()["detail"] == "Sesión expirada"


# ── TC4: JWT expirado → 401 ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_admin_jwt_expirado_retorna_401() -> None:
    if not SECRET_KEY:
        pytest.skip("SECRET_KEY no configurada")

    pasado = datetime.now(timezone.utc) - timedelta(hours=9)
    token_expirado = jwt.encode(
        {"sub": "admin@vent3.test", "iat": pasado, "exp": pasado + timedelta(hours=8)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    async with AsyncClient(transport=ASGITransport(app=_admin_app), base_url="http://test") as client:
        client.cookies.set(COOKIE_NAME, token_expirado)
        response = await client.get("/test-protegido")

    assert response.status_code == 401
    assert response.json()["detail"] == "Sesión expirada"


# ── TC5: usuario inactivo → 401 ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_admin_usuario_inactivo_retorna_401(db_ok: None) -> None:
    if not SECRET_KEY:
        pytest.skip("SECRET_KEY no configurada")

    test_email = "inactivo_tc5_autorizacion@vent3.test"
    password_hash = bcrypt.hashpw(b"test-pass-tc5-xyz", bcrypt.gensalt(rounds=4)).decode()
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with factory() as session:
            await session.execute(
                text(
                    "INSERT INTO usuarios (id, email, nombre, password_hash, rol, activo, intentos_fallidos, created_at) "
                    "VALUES (gen_random_uuid(), :email, 'Test Inactivo TC5', :hash, 'admin', TRUE, 0, NOW())"
                ),
                {"email": test_email, "hash": password_hash},
            )
            await session.commit()

        token = crear_access_token({"sub": test_email})

        async with factory() as session:
            await session.execute(
                text("UPDATE usuarios SET activo = FALSE WHERE email = :email"),
                {"email": test_email},
            )
            await session.commit()

        async with AsyncClient(transport=ASGITransport(app=_admin_app), base_url="http://test") as client:
            client.cookies.set(COOKIE_NAME, token)
            response = await client.get("/test-protegido")

        assert response.status_code == 401
        assert response.json()["detail"] == "Usuario inactivo"

    finally:
        async with factory() as session:
            await session.execute(
                text("DELETE FROM usuarios WHERE email = :email"),
                {"email": test_email},
            )
            await session.commit()
        await engine.dispose()
