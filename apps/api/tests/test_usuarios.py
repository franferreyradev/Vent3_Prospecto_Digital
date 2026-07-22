"""
Tests de integración para el listado/gestión de usuarios (admin-only).

Requieren la DB de test con el admin seed de T3 aplicado.
"""

import os

import bcrypt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.security import COOKIE_NAME, crear_access_token
from src.main import app

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")


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


def _factory():
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _crear_usuario(factory, email: str, rol: str = "editor") -> str:
    password_hash = bcrypt.hashpw(b"usuario-test-pass-xyz", bcrypt.gensalt(rounds=4)).decode()
    async with factory() as session:
        result = await session.execute(
            text(
                "INSERT INTO usuarios (id, email, nombre, password_hash, rol, activo, intentos_fallidos, created_at) "
                "VALUES (gen_random_uuid(), :email, 'Usuario Test', :hash, :rol, TRUE, 0, NOW()) RETURNING id"
            ),
            {"email": email, "hash": password_hash, "rol": rol},
        )
        usuario_id = str(result.scalar_one())
        await session.commit()
    return usuario_id


async def _limpiar(factory, emails: list[str]) -> None:
    async with factory() as session:
        for email in emails:
            await session.execute(text("DELETE FROM usuarios WHERE email = :email"), {"email": email})
        await session.commit()


# ── Listado ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_usuarios_como_admin_ok(db_ok: None) -> None:
    if not ADMIN_EMAIL:
        pytest.skip("ADMIN_EMAIL no configurada")

    token = crear_access_token({"sub": ADMIN_EMAIL})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.cookies.set(COOKIE_NAME, token)
        response = await client.get("/api/usuarios")

    assert response.status_code == 200
    data = response.json()
    assert any(u["email"] == ADMIN_EMAIL for u in data["data"])


@pytest.mark.asyncio
async def test_listar_usuarios_como_editor_retorna_403(db_ok: None) -> None:
    engine, factory = _factory()
    email = "editor_listado_tc2@qa.vent3.com.ar"

    try:
        await _crear_usuario(factory, email, rol="editor")
        token = crear_access_token({"sub": email})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set(COOKIE_NAME, token)
            response = await client.get("/api/usuarios")

        assert response.status_code == 403
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


# ── Cambiar estado ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_desactivar_usuario_bloquea_login_posterior(db_ok: None) -> None:
    if not ADMIN_EMAIL:
        pytest.skip("ADMIN_EMAIL no configurada")

    engine, factory = _factory()
    email = "desactivar_tc3@qa.vent3.com.ar"

    try:
        usuario_id = await _crear_usuario(factory, email, rol="editor")
        admin_token = crear_access_token({"sub": ADMIN_EMAIL})
        usuario_token = crear_access_token({"sub": email})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set(COOKIE_NAME, admin_token)
            response = await client.patch(
                f"/api/usuarios/{usuario_id}/estado", json={"activo": False}
            )
            assert response.status_code == 200
            assert response.json()["activo"] is False

            client.cookies.set(COOKIE_NAME, usuario_token)
            me_r = await client.get("/api/auth/me")
            assert me_r.status_code == 401
            assert me_r.json()["detail"] == "Usuario inactivo"

            # También bloquea un login nuevo, no solo una sesión ya emitida
            # (el endpoint de login debe chequear activo, no solo password/lockout).
            client.cookies.delete(COOKIE_NAME)
            login_r = await client.post(
                "/api/auth/login",
                json={"email": email, "password": "usuario-test-pass-xyz"},
            )
            assert login_r.status_code == 401
            assert login_r.json()["detail"] == "Usuario inactivo"
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


@pytest.mark.asyncio
async def test_admin_no_puede_desactivarse_a_si_mismo_retorna_409(db_ok: None) -> None:
    if not ADMIN_EMAIL:
        pytest.skip("ADMIN_EMAIL no configurada")

    engine, factory = _factory()
    admin_id = None

    try:
        async with factory() as session:
            result = await session.execute(
                text("SELECT id FROM usuarios WHERE email = :email"), {"email": ADMIN_EMAIL}
            )
            admin_id = str(result.scalar_one())

        token = crear_access_token({"sub": ADMIN_EMAIL})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set(COOKIE_NAME, token)
            response = await client.patch(
                f"/api/usuarios/{admin_id}/estado", json={"activo": False}
            )

        assert response.status_code == 409
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_reactivar_usuario_permite_login_nuevamente(db_ok: None) -> None:
    if not ADMIN_EMAIL:
        pytest.skip("ADMIN_EMAIL no configurada")

    engine, factory = _factory()
    email = "reactivar_tc5@qa.vent3.com.ar"

    try:
        usuario_id = await _crear_usuario(factory, email, rol="editor")
        admin_token = crear_access_token({"sub": ADMIN_EMAIL})
        usuario_token = crear_access_token({"sub": email})

        async with factory() as session:
            await session.execute(
                text("UPDATE usuarios SET activo = FALSE WHERE email = :email"), {"email": email}
            )
            await session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set(COOKIE_NAME, admin_token)
            response = await client.patch(
                f"/api/usuarios/{usuario_id}/estado", json={"activo": True}
            )
            assert response.status_code == 200
            assert response.json()["activo"] is True

            client.cookies.set(COOKIE_NAME, usuario_token)
            me_r = await client.get("/api/auth/me")
            assert me_r.status_code == 200
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()
