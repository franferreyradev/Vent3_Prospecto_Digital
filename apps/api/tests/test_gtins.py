"""
Tests de integración para PATCH /api/gtins/{id} (gap de T25/T26).

Patrón NullPool establecido en T7 (test_autorizacion.py): cada request
usa una conexión nueva para evitar "Future attached to different loop"
con pytest-asyncio. Mismo fixture shape que test_productos.py.
"""

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.db import get_db
from src.core.security import COOKIE_NAME
from src.main import app

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
async def gtin_seed():
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sufijo = uuid.uuid4().hex[:8]
    producto_id = uuid.uuid4()
    gtin_id = uuid.uuid4()
    gtin_numero = f"029{uuid.uuid4().int % 10**11:011d}"

    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO productos "
                "(id, codigo_interno, nombre_comercial, forma_farmaceutica, "
                "presentacion_cantidad, canal, estado, tiene_prospecto, created_at, updated_at) "
                "VALUES (:id, :codigo_interno, :nombre_comercial, 'comprimidos', "
                "'x30', 'farmacia', 'activo', FALSE, NOW(), NOW())"
            ),
            {
                "id": producto_id,
                "codigo_interno": f"T25-{sufijo}",
                "nombre_comercial": f"PRODUCTO GTIN TEST {sufijo}",
            },
        )
        await session.execute(
            text(
                "INSERT INTO gtin_registro "
                "(id, producto_id, gtin, estado_gtin, es_vigente, url_digital_link, "
                "qr_generado, validado_gs1, created_at) "
                "VALUES (:id, :producto_id, :gtin, 'en_desarrollo', TRUE, NULL, "
                "FALSE, FALSE, NOW())"
            ),
            {"id": gtin_id, "producto_id": producto_id, "gtin": gtin_numero},
        )
        await session.commit()

    yield {"gtin_id": gtin_id, "producto_id": producto_id, "gtin": gtin_numero}

    # audit_log es append-only: no se borra, solo productos (gtin_registro cae en cascada por FK).
    async with factory() as session:
        await session.execute(
            text("DELETE FROM gtin_registro WHERE id = :id"), {"id": gtin_id}
        )
        await session.execute(
            text("DELETE FROM productos WHERE id = :id"), {"id": producto_id}
        )
        await session.commit()
    await engine.dispose()


# ── TC1: sin autenticación → 401 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_actualizar_gtin_sin_autenticacion_retorna_401(client: AsyncClient) -> None:
    response = await client.patch(
        f"/api/gtins/{uuid.uuid4()}", json={"qr_generado": True}
    )
    assert response.status_code == 401


# ── TC2: GTIN inexistente → 404 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_actualizar_gtin_inexistente_retorna_404(auth_client: AsyncClient) -> None:
    response = await auth_client.patch(
        f"/api/gtins/{uuid.uuid4()}", json={"qr_generado": True}
    )
    assert response.status_code == 404


# ── TC3: PATCH actualiza url_digital_link + qr_generado y audita ambos campos ──


@pytest.mark.asyncio
async def test_actualizar_gtin_setea_url_y_qr_generado_y_audita(
    auth_client: AsyncClient, gtin_seed
) -> None:
    gtin_id = gtin_seed["gtin_id"]
    url = f"https://www.vent3.com.ar/01/{gtin_seed['gtin']}"

    response = await auth_client.patch(
        f"/api/gtins/{gtin_id}",
        json={"url_digital_link": url, "qr_generado": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["url_digital_link"] == url
    assert body["qr_generado"] is True

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT campo_modificado, valor_nuevo FROM audit_log "
                    "WHERE registro_id = :id AND tabla_afectada = 'gtin_registro' "
                    "ORDER BY campo_modificado"
                ),
                {"id": str(gtin_id)},
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    assert len(rows) == 2
    campos = {r[0]: r[1] for r in rows}
    assert campos["qr_generado"] == "True"
    assert campos["url_digital_link"] == url


# ── TC4: PATCH setea validado_gs1 (flujo de T26) y audita ─────────────────


@pytest.mark.asyncio
async def test_actualizar_gtin_setea_validado_gs1_y_audita(
    auth_client: AsyncClient, gtin_seed
) -> None:
    gtin_id = gtin_seed["gtin_id"]

    response = await auth_client.patch(
        f"/api/gtins/{gtin_id}", json={"validado_gs1": True}
    )

    assert response.status_code == 200
    assert response.json()["validado_gs1"] is True

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT campo_modificado, valor_nuevo FROM audit_log "
                    "WHERE registro_id = :id AND tabla_afectada = 'gtin_registro'"
                ),
                {"id": str(gtin_id)},
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    assert len(rows) == 1
    assert rows[0][0] == "validado_gs1"
    assert rows[0][1] == "True"
