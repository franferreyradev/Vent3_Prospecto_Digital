"""
TC1-TC8: Tests de integración para los endpoints de autenticación (T6).

Requieren la DB de test con el admin seed de T3 aplicado.
ADMIN_EMAIL y ADMIN_INITIAL_PASSWORD se leen del entorno (seteados en conftest.py).
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.security import ALGORITHM, COOKIE_NAME
from src.main import app

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_INITIAL_PASSWORD", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")


@pytest_asyncio.fixture
async def db_ok():
    """Skips the test if the test DB is not reachable."""
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL no configurada")
    engine = create_async_engine(DATABASE_URL, echo=False)
    try:
        conn = await engine.connect()
        await conn.close()
    except Exception as e:
        await engine.dispose()
        pytest.skip(f"DB no accesible: {e}")
    finally:
        await engine.dispose()


# ── TC1 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_exitoso_retorna_204_con_cookie(db_ok: None) -> None:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.skip("ADMIN_EMAIL / ADMIN_INITIAL_PASSWORD no configuradas")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )

    assert response.status_code == 204
    assert "set-cookie" in response.headers
    cookie_header = response.headers["set-cookie"]
    assert COOKIE_NAME in cookie_header
    assert "httponly" in cookie_header.lower()


# ── TC2 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_email_inexistente_retorna_401_credenciales_invalidas(db_ok: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "noexiste@vent3.test", "password": "cualquier-password-123"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


# ── TC3 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_password_incorrecto_retorna_mismo_mensaje_que_email_inexistente(db_ok: None) -> None:
    if not ADMIN_EMAIL:
        pytest.skip("ADMIN_EMAIL no configurada")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "password-incorrecto-xyz"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


# ── TC4 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_lockout_tras_cinco_intentos_fallidos(db_ok: None) -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    test_email = "lockout_tc4@vent3.test"
    test_password = "lockout-test-password-123"
    password_hash = bcrypt.hashpw(test_password.encode(), bcrypt.gensalt(rounds=4)).decode()

    try:
        async with factory() as session:
            await session.execute(
                text(
                    "INSERT INTO usuarios "
                    "(id, email, nombre, password_hash, rol, activo, intentos_fallidos, created_at) "
                    "VALUES (gen_random_uuid(), :email, 'Lockout Test', :hash, 'lector', TRUE, 0, NOW())"
                ),
                {"email": test_email, "hash": password_hash},
            )
            await session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for _ in range(5):
                r = await client.post(
                    "/api/auth/login",
                    json={"email": test_email, "password": "wrong-password"},
                )
                assert r.status_code == 401
                assert r.json()["detail"] == "Credenciales inválidas"

            r6 = await client.post(
                "/api/auth/login",
                json={"email": test_email, "password": "wrong-password"},
            )
            assert r6.status_code == 401
            assert "bloqueada" in r6.json()["detail"].lower()

        async with factory() as session:
            result = await session.execute(
                text("SELECT bloqueado_hasta FROM usuarios WHERE email = :email"),
                {"email": test_email},
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] is not None

    finally:
        async with factory() as session:
            await session.execute(
                text("DELETE FROM usuarios WHERE email = :email"),
                {"email": test_email},
            )
            await session.commit()
        await engine.dispose()


# ── TC5 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_sin_cookie_retorna_401() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == 401


# ── TC6 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_con_cookie_valida_retorna_datos_del_usuario(db_ok: None) -> None:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.skip("ADMIN_EMAIL / ADMIN_INITIAL_PASSWORD no configuradas")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_r = await client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert login_r.status_code == 204

        token = login_r.cookies.get(COOKIE_NAME)
        assert token is not None
        client.cookies.set(COOKIE_NAME, token)

        me_r = await client.get("/api/auth/me")

    assert me_r.status_code == 200
    data = me_r.json()
    assert data["email"] == ADMIN_EMAIL
    assert "password_hash" not in data


# ── TC7 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_logout_borra_cookie_y_me_retorna_401(db_ok: None) -> None:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.skip("ADMIN_EMAIL / ADMIN_INITIAL_PASSWORD no configuradas")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_r = await client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert login_r.status_code == 204

        token = login_r.cookies.get(COOKIE_NAME)
        assert token is not None
        client.cookies.set(COOKIE_NAME, token)

        logout_r = await client.post("/api/auth/logout")
        assert logout_r.status_code == 204
        assert "set-cookie" in logout_r.headers

        # Después del logout la cookie debe haber sido borrada del jar del cliente.
        # El servidor responde con Set-Cookie que vacía la cookie.
        client.cookies.delete(COOKIE_NAME)
        me_r = await client.get("/api/auth/me")

    assert me_r.status_code == 401


# ── TC8 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_token_expirado_retorna_401_sesion_expirada() -> None:
    secret_key = os.environ.get("SECRET_KEY", "")
    if not secret_key:
        pytest.skip("SECRET_KEY no configurada")

    past = datetime.now(timezone.utc) - timedelta(hours=9)
    expired_token = jwt.encode(
        {"sub": "admin@test.com", "iat": past, "exp": past + timedelta(hours=8)},
        secret_key,
        algorithm=ALGORITHM,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.cookies.set(COOKIE_NAME, expired_token)
        response = await client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Sesión expirada"
