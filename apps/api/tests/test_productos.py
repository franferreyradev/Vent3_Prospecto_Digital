"""
TC1-TC10: Tests de integración para los endpoints de productos (T9).

Patrón NullPool establecido en T7 (test_autorizacion.py): cada request
usa una conexión nueva para evitar "Future attached to different loop"
con pytest-asyncio.
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
async def productos_seed():
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sufijo = uuid.uuid4().hex[:8]
    ids = [uuid.uuid4() for _ in range(3)]
    productos = [
        {
            "id": ids[0],
            "codigo_interno": f"T9-A1-{sufijo}",
            "nombre_comercial": f"PRODUCTO ACTIVO UNO {sufijo}",
            "estado": "activo",
            "canal": "farmacia",
        },
        {
            "id": ids[1],
            "codigo_interno": f"T9-A2-{sufijo}",
            "nombre_comercial": f"PRODUCTO ACTIVO DOS {sufijo}",
            "estado": "activo",
            "canal": "farmacia",
        },
        {
            "id": ids[2],
            "codigo_interno": f"T9-INA-{sufijo}",
            "nombre_comercial": f"PRODUCTO INACTIVO {sufijo}",
            "estado": "inactivo",
            "canal": "farmacia",
        },
    ]

    async with factory() as session:
        for p in productos:
            await session.execute(
                text(
                    "INSERT INTO productos "
                    "(id, codigo_interno, nombre_comercial, forma_farmaceutica, "
                    "presentacion_cantidad, canal, estado, tiene_prospecto, created_at, updated_at) "
                    "VALUES (:id, :codigo_interno, :nombre_comercial, 'comprimidos', "
                    "'x30', :canal, :estado, FALSE, NOW(), NOW())"
                ),
                p,
            )
        await session.commit()

    yield productos

    # audit_log es append-only (inmutable a nivel de DB): no se borra, solo productos.
    async with factory() as session:
        await session.execute(
            text("DELETE FROM productos WHERE id = ANY(:ids)"),
            {"ids": [str(i) for i in ids]},
        )
        await session.commit()
    await engine.dispose()


# ── TC1: sin autenticación → 401 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_productos_sin_autenticacion_retorna_401(client: AsyncClient) -> None:
    response = await client.get("/api/productos")
    assert response.status_code == 401


# ── TC2: listado paginado con admin ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_productos_con_admin_retorna_200_paginado(
    auth_client: AsyncClient, productos_seed
) -> None:
    response = await auth_client.get("/api/productos")

    assert response.status_code == 200
    body = response.json()
    assert "data" in body and "total" in body and "page" in body and "limit" in body
    assert isinstance(body["data"], list)
    if body["data"]:
        item = body["data"][0]
        for campo in (
            "id",
            "codigo_interno",
            "nombre_comercial",
            "forma_farmaceutica",
            "presentacion_cantidad",
            "canal",
            "estado",
            "tiene_prospecto",
        ):
            assert campo in item


# ── TC3: filtro por estado=activo ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_productos_filtro_estado_activo_excluye_inactivos(
    auth_client: AsyncClient, productos_seed
) -> None:
    sufijo = productos_seed[0]["codigo_interno"].split("-")[-1]

    response = await auth_client.get(
        "/api/productos", params={"estado": "activo", "search": sufijo, "limit": 200}
    )

    assert response.status_code == 200
    nombres = [item["nombre_comercial"] for item in response.json()["data"]]
    assert any("ACTIVO UNO" in n for n in nombres)
    assert not any("INACTIVO" in n for n in nombres)


# ── TC4: filtro por search ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_productos_filtro_search_filtra_por_nombre(
    auth_client: AsyncClient, productos_seed
) -> None:
    sufijo = productos_seed[0]["codigo_interno"].split("-")[-1]

    response = await auth_client.get(
        "/api/productos", params={"search": f"ACTIVO UNO {sufijo}"}
    )

    assert response.status_code == 200
    nombres = [item["nombre_comercial"] for item in response.json()["data"]]
    assert any("ACTIVO UNO" in n for n in nombres)
    assert not any("ACTIVO DOS" in n for n in nombres)


# ── TC5: paginación ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_productos_paginacion(auth_client: AsyncClient, productos_seed) -> None:
    sufijo = productos_seed[0]["codigo_interno"].split("-")[-1]

    r1 = await auth_client.get(
        "/api/productos", params={"search": sufijo, "page": 1, "limit": 2}
    )
    r2 = await auth_client.get(
        "/api/productos", params={"search": sufijo, "page": 2, "limit": 2}
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["total"] == 3
    assert len(r1.json()["data"]) == 2
    assert len(r2.json()["data"]) == 1


# ── TC6: detalle existente ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_obtener_producto_existente_retorna_200_con_detalle(
    auth_client: AsyncClient, productos_seed
) -> None:
    producto_id = productos_seed[0]["id"]

    response = await auth_client.get(f"/api/productos/{producto_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(producto_id)
    assert "principios" in body
    assert isinstance(body["principios"], list)
    assert "gtin_registros" in body
    assert isinstance(body["gtin_registros"], list)


# ── TC7: detalle inexistente ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_obtener_producto_inexistente_retorna_404(auth_client: AsyncClient) -> None:
    response = await auth_client.get(f"/api/productos/{uuid.uuid4()}")
    assert response.status_code == 404


# ── TC8: PATCH modifica nombre_comercial y audita ─────────────────────────


@pytest.mark.asyncio
async def test_actualizar_producto_modifica_nombre_y_audita(
    auth_client: AsyncClient, productos_seed
) -> None:
    producto_id = productos_seed[0]["id"]

    response = await auth_client.patch(
        f"/api/productos/{producto_id}",
        json={"nombre_comercial": "NUEVO NOMBRE TEST"},
    )

    assert response.status_code == 200
    assert response.json()["nombre_comercial"] == "NUEVO NOMBRE TEST"

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT campo_modificado, valor_anterior, valor_nuevo FROM audit_log "
                    "WHERE registro_id = :id AND tabla_afectada = 'productos'"
                ),
                {"id": str(producto_id)},
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    assert len(rows) == 1
    assert rows[0][0] == "nombre_comercial"
    assert rows[0][2] == "NUEVO NOMBRE TEST"


# ── TC9: PATCH estado desactiva y audita ──────────────────────────────────


@pytest.mark.asyncio
async def test_cambiar_estado_desactiva_producto_y_audita(
    auth_client: AsyncClient, productos_seed
) -> None:
    producto_id = productos_seed[0]["id"]

    response = await auth_client.patch(
        f"/api/productos/{producto_id}/estado", json={"estado": "inactivo"}
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "inactivo"

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT campo_modificado, valor_anterior, valor_nuevo FROM audit_log "
                    "WHERE registro_id = :id AND campo_modificado = 'estado'"
                ),
                {"id": str(producto_id)},
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    assert len(rows) == 1
    assert rows[0][1] == "activo"
    assert rows[0][2] == "inactivo"


# ── TC10: PATCH estado idempotente ────────────────────────────────────────


@pytest.mark.asyncio
async def test_cambiar_estado_idempotente_no_duplica_auditoria(
    auth_client: AsyncClient, productos_seed
) -> None:
    producto_id = productos_seed[2]["id"]  # ya inactivo en el seed

    response = await auth_client.patch(
        f"/api/productos/{producto_id}/estado", json={"estado": "inactivo"}
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "inactivo"

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT COUNT(*) FROM audit_log "
                    "WHERE registro_id = :id AND campo_modificado = 'estado'"
                ),
                {"id": str(producto_id)},
            )
            total = result.scalar_one()
    finally:
        await engine.dispose()

    assert total == 0
