"""
Tests de integración para gestión de usuarios vía invitación de un solo uso
(ver docs/adr/003-gestion-usuarios-post-mvp.md).

Requieren la DB de test con el admin seed de T3 aplicado.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.security import COOKIE_NAME, crear_access_token, generar_token_invitacion, hash_token
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


async def _admin_id(factory) -> str:
    async with factory() as session:
        result = await session.execute(
            text("SELECT id FROM usuarios WHERE email = :email"), {"email": ADMIN_EMAIL}
        )
        return str(result.scalar_one())


async def _crear_usuario_editor(factory, email: str) -> None:
    password_hash = bcrypt.hashpw(b"editor-test-pass-xyz", bcrypt.gensalt(rounds=4)).decode()
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO usuarios (id, email, nombre, password_hash, rol, activo, intentos_fallidos, created_at) "
                "VALUES (gen_random_uuid(), :email, 'Editor Test', :hash, 'editor', TRUE, 0, NOW())"
            ),
            {"email": email, "hash": password_hash},
        )
        await session.commit()


async def _insertar_invitacion(
    factory,
    email: str,
    token_plano: str,
    rol: str = "editor",
    expira_en: datetime | None = None,
    usado_en: datetime | None = None,
) -> None:
    admin_id = await _admin_id(factory)
    if expira_en is None:
        expira_en = datetime.now(timezone.utc) + timedelta(hours=48)
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO invitaciones_usuario "
                "(id, email, nombre, rol, token_hash, creado_por, expira_en, usado_en) "
                "VALUES (gen_random_uuid(), :email, 'Invitado Test', :rol, :token_hash, :creado_por, :expira_en, :usado_en)"
            ),
            {
                "email": email,
                "rol": rol,
                "token_hash": hash_token(token_plano),
                "creado_por": admin_id,
                "expira_en": expira_en,
                "usado_en": usado_en,
            },
        )
        await session.commit()


async def _limpiar(factory, emails: list[str]) -> None:
    # audit_log es append-only con FK RESTRICT hacia usuarios (CLAUDE.md prohíbe
    # DELETE en tablas de negocio) — cualquier email que haya pasado por
    # /activar (o generado un evento de auditoría como actor) queda con una fila
    # en audit_log que no se puede borrar. Mismo patrón que test_gtins.py: no se
    # borra el usuario, se desactiva (soft-delete); los emails son únicos por
    # corrida (sufijo uuid4) así un rerun nunca choca con el 409 de email
    # duplicado.
    async with factory() as session:
        for email in emails:
            await session.execute(
                text("DELETE FROM invitaciones_usuario WHERE email = :email"), {"email": email}
            )
            await session.execute(
                text("UPDATE usuarios SET activo = FALSE WHERE email = :email"),
                {"email": email},
            )
        await session.commit()


# ── Crear invitación ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_crear_invitacion_como_admin_retorna_link_con_token(db_ok: None) -> None:
    if not ADMIN_EMAIL:
        pytest.skip("ADMIN_EMAIL no configurada")

    engine, factory = _factory()
    email = "nuevo_editor_tc1@qa.vent3.com.ar"
    token = crear_access_token({"sub": ADMIN_EMAIL})

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set(COOKIE_NAME, token)
            response = await client.post(
                "/api/invitaciones",
                json={"email": email, "nombre": "Nuevo Editor", "rol": "editor"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert f"/activar-invitacion/" in data["link"]
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


@pytest.mark.asyncio
async def test_crear_invitacion_como_editor_retorna_403(db_ok: None) -> None:
    engine, factory = _factory()
    editor_email = f"editor_tc2_{uuid.uuid4().hex[:8]}@qa.vent3.com.ar"
    invitado_email = "invitado_tc2@qa.vent3.com.ar"

    try:
        await _crear_usuario_editor(factory, editor_email)
        token = crear_access_token({"sub": editor_email})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set(COOKIE_NAME, token)
            response = await client.post(
                "/api/invitaciones",
                json={"email": invitado_email, "nombre": "Invitado", "rol": "editor"},
            )

        assert response.status_code == 403
    finally:
        await _limpiar(factory, [editor_email, invitado_email])
        await engine.dispose()


@pytest.mark.asyncio
async def test_crear_invitacion_con_email_de_usuario_existente_retorna_409(db_ok: None) -> None:
    if not ADMIN_EMAIL:
        pytest.skip("ADMIN_EMAIL no configurada")

    engine, factory = _factory()
    token = crear_access_token({"sub": ADMIN_EMAIL})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.cookies.set(COOKIE_NAME, token)
        response = await client.post(
            "/api/invitaciones",
            json={"email": ADMIN_EMAIL, "nombre": "Admin Duplicado", "rol": "admin"},
        )

    await engine.dispose()
    assert response.status_code == 409


# ── Validar token ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validar_token_valido_retorna_email_y_rol(db_ok: None) -> None:
    engine, factory = _factory()
    email = "validar_tc4@qa.vent3.com.ar"
    token_plano = generar_token_invitacion()

    try:
        await _insertar_invitacion(factory, email, token_plano, rol="editor")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/invitaciones/validar/{token_plano}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert data["rol"] == "editor"
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


@pytest.mark.asyncio
async def test_validar_token_inexistente_retorna_404_generico() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/invitaciones/validar/token-que-no-existe")

    assert response.status_code == 404
    assert response.json()["detail"] == "Invitación inválida o expirada"


@pytest.mark.asyncio
async def test_validar_token_expirado_retorna_mismo_404_generico(db_ok: None) -> None:
    engine, factory = _factory()
    email = "expirado_tc6@qa.vent3.com.ar"
    token_plano = generar_token_invitacion()

    try:
        await _insertar_invitacion(
            factory,
            email,
            token_plano,
            expira_en=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/invitaciones/validar/{token_plano}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Invitación inválida o expirada"
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


@pytest.mark.asyncio
async def test_validar_token_ya_usado_retorna_mismo_404_generico(db_ok: None) -> None:
    engine, factory = _factory()
    email = "usado_tc7@qa.vent3.com.ar"
    token_plano = generar_token_invitacion()

    try:
        await _insertar_invitacion(
            factory, email, token_plano, usado_en=datetime.now(timezone.utc)
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/invitaciones/validar/{token_plano}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Invitación inválida o expirada"
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


# ── Activar invitación ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_activar_invitacion_crea_usuario_y_setea_cookie(db_ok: None) -> None:
    engine, factory = _factory()
    # Sufijo único: la activación genera un usuario auditado (soft-delete only,
    # nunca DELETE) — un email fijo chocaría con 409 en la segunda corrida.
    email = f"activar_tc8_{uuid.uuid4().hex[:8]}@qa.vent3.com.ar"
    token_plano = generar_token_invitacion()

    try:
        await _insertar_invitacion(factory, email, token_plano, rol="editor")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/invitaciones/{token_plano}/activar",
                json={"password": "password-nuevo-usuario-123"},
            )

        assert response.status_code == 200
        assert "set-cookie" in response.headers
        assert COOKIE_NAME in response.headers["set-cookie"]
        data = response.json()
        assert data["email"] == email
        assert data["rol"] == "editor"

        async with factory() as session:
            result = await session.execute(
                text("SELECT usado_en FROM invitaciones_usuario WHERE email = :email"),
                {"email": email},
            )
            assert result.scalar_one() is not None
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


@pytest.mark.asyncio
async def test_activar_invitacion_dos_veces_segunda_falla(db_ok: None) -> None:
    engine, factory = _factory()
    email = f"activar_dos_veces_tc9_{uuid.uuid4().hex[:8]}@qa.vent3.com.ar"
    token_plano = generar_token_invitacion()

    try:
        await _insertar_invitacion(factory, email, token_plano, rol="editor")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r1 = await client.post(
                f"/api/invitaciones/{token_plano}/activar",
                json={"password": "password-nuevo-usuario-123"},
            )
            assert r1.status_code == 200

            r2 = await client.post(
                f"/api/invitaciones/{token_plano}/activar",
                json={"password": "otra-password-distinta-456"},
            )

        assert r2.status_code == 404
        assert r2.json()["detail"] == "Invitación inválida o expirada"
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()


@pytest.mark.asyncio
async def test_activar_invitacion_con_password_corta_retorna_422(db_ok: None) -> None:
    engine, factory = _factory()
    email = "password_corta_tc10@qa.vent3.com.ar"
    token_plano = generar_token_invitacion()

    try:
        await _insertar_invitacion(factory, email, token_plano, rol="editor")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/invitaciones/{token_plano}/activar",
                json={"password": "corta"},
            )

        assert response.status_code == 422
    finally:
        await _limpiar(factory, [email])
        await engine.dispose()
