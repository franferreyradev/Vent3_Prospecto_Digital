"""
TC1-TC6: Tests de integración para GET /api/audit-log (T13).

Patrón NullPool establecido en T7 (test_autorizacion.py) / T9
(test_productos.py). audit_log es append-only a nivel de DB (trigger
bloquea UPDATE/DELETE) — el seed usa AuditoriaService.registrar_cambio()
directo y el teardown NO borra las filas sembradas.
"""

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.db import get_db
from src.core.security import COOKIE_NAME
from src.main import app
from src.services.auditoria import AuditoriaService

DATABASE_URL = os.environ.get("DATABASE_URL", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_INITIAL_PASSWORD", "")


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


app.dependency_overrides[get_db] = _get_db_nullpool


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


@pytest_asyncio.fixture
async def client(db_ok: None) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.skip("ADMIN_EMAIL / ADMIN_INITIAL_PASSWORD no configuradas")

    login_r = await client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert login_r.status_code == 204
    token = login_r.cookies.get(COOKIE_NAME)
    assert token is not None
    client.cookies.set(COOKIE_NAME, token)
    return client


@pytest_asyncio.fixture
async def audit_seed():
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sufijo = uuid.uuid4().hex[:8]
    tabla_a = f"t13_tabla_a_{sufijo}"
    tabla_b = f"t13_tabla_b_{sufijo}"
    registro_a1 = uuid.uuid4()
    registro_a2 = uuid.uuid4()
    registro_b = uuid.uuid4()

    async with factory() as session:
        result = await session.execute(
            text("SELECT id FROM usuarios WHERE email = :email"),
            {"email": ADMIN_EMAIL},
        )
        row = result.fetchone()
        if row is None:
            pytest.skip(f"Usuario {ADMIN_EMAIL} no encontrado en DB de test")
        usuario_id = row[0]

        auditoria = AuditoriaService(session)
        await auditoria.registrar_cambio(
            tabla=tabla_a,
            registro_id=registro_a1,
            accion="UPDATE",
            usuario_id=usuario_id,
            campo="nombre",
            valor_anterior="viejo",
            valor_nuevo="nuevo",
        )
        await auditoria.registrar_cambio(
            tabla=tabla_a,
            registro_id=registro_a2,
            accion="UPDATE",
            usuario_id=usuario_id,
            campo="nombre",
            valor_anterior="viejo2",
            valor_nuevo="nuevo2",
        )
        await auditoria.registrar_cambio(
            tabla=tabla_b,
            registro_id=registro_b,
            accion="UPDATE",
            usuario_id=usuario_id,
            campo="estado",
            valor_anterior="activo",
            valor_nuevo="inactivo",
        )
        await session.commit()

    yield {
        "sufijo": sufijo,
        "tabla_a": tabla_a,
        "tabla_b": tabla_b,
        "usuario_id": usuario_id,
        "registro_a1": registro_a1,
        "registro_a2": registro_a2,
        "registro_b": registro_b,
    }

    # audit_log es append-only (inmutable a nivel de DB): no se borra nada.
    await engine.dispose()


# ── TC1: sin autenticación → 401 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_audit_log_sin_autenticacion_retorna_401(client: AsyncClient) -> None:
    response = await client.get("/api/audit-log")
    assert response.status_code == 401


# ── TC2: autenticado sin filtros → 200 paginado ───────────────────────────────


@pytest.mark.asyncio
async def test_listar_audit_log_con_admin_retorna_200_paginado(
    auth_client: AsyncClient, audit_seed
) -> None:
    response = await auth_client.get("/api/audit-log")

    assert response.status_code == 200
    body = response.json()
    assert "data" in body and "total" in body and "page" in body and "limit" in body
    assert isinstance(body["data"], list)
    assert body["total"] >= 2


# ── TC3: filtro por tabla ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_audit_log_filtro_tabla_separa_registros(
    auth_client: AsyncClient, audit_seed
) -> None:
    response_a = await auth_client.get(
        "/api/audit-log", params={"tabla": audit_seed["tabla_a"]}
    )
    response_b = await auth_client.get(
        "/api/audit-log", params={"tabla": audit_seed["tabla_b"]}
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    body_a = response_a.json()
    body_b = response_b.json()
    assert body_a["total"] == 2
    assert all(item["tabla_afectada"] == audit_seed["tabla_a"] for item in body_a["data"])
    assert body_b["total"] == 1
    assert body_b["data"][0]["tabla_afectada"] == audit_seed["tabla_b"]


# ── TC4: filtro por rango de fechas ───────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_audit_log_filtro_fechas_excluye_fuera_de_rango(
    auth_client: AsyncClient, audit_seed
) -> None:
    futuro = datetime.now(timezone.utc) + timedelta(days=1)

    response = await auth_client.get(
        "/api/audit-log",
        params={"tabla": audit_seed["tabla_a"], "desde": futuro.isoformat()},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


# ── TC5: paginación ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_audit_log_paginacion(auth_client: AsyncClient, audit_seed) -> None:
    response = await auth_client.get(
        "/api/audit-log", params={"tabla": audit_seed["tabla_a"], "limit": 1}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["data"]) == 1


# ── TC6: método no permitido → 405 ────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_audit_log_retorna_405(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/audit-log", json={})
    assert response.status_code == 405
