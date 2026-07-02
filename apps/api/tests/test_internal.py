"""
TC1-TC8: Tests de integración para el endpoint interno de resolución
GTIN → prospectos (T12).

Patrón NullPool establecido en T7/T11. Este endpoint NO usa cookies de
sesión: se autentica con el header X-Internal-Token, comparado en
tiempo constante contra settings.INTERNAL_API_TOKEN. auth_client solo
se usa para armar el seed de prospectos vigentes vía los endpoints ya
existentes de T11 (POST /api/prospectos + PATCH /activar), reutilizando
ese flujo en vez de insertar prospectos por SQL directo.
"""

import os
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch

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
INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")

PDF_VALIDO = b"%PDF-1.4\n%mock prospecto de prueba\n%%EOF"


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


@pytest.fixture(autouse=True)
def mock_r2():
    with patch("src.services.storage.r2") as mock:
        yield mock


def _gtin() -> str:
    return str(uuid.uuid4().int)[:14].ljust(14, "0")


@pytest_asyncio.fixture
async def gtin_seed():
    if not INTERNAL_API_TOKEN:
        pytest.skip("INTERNAL_API_TOKEN no configurada")
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL no configurada")

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sufijo = uuid.uuid4().hex[:8]
    producto_id = uuid.uuid4()
    gtin = _gtin()

    async def _crear(estado: str = "activo"):
        async with factory() as session:
            await session.execute(
                text(
                    "INSERT INTO productos "
                    "(id, codigo_interno, nombre_comercial, forma_farmaceutica, "
                    "presentacion_cantidad, canal, estado, tiene_prospecto, created_at, updated_at) "
                    "VALUES (:id, :codigo_interno, :nombre, 'comprimidos', 'x30', "
                    "'farmacia', :estado, FALSE, NOW(), NOW())"
                ),
                {
                    "id": producto_id,
                    "codigo_interno": f"T12-{sufijo}",
                    "nombre": f"PRODUCTO T12 {sufijo}",
                    "estado": estado,
                },
            )
            await session.execute(
                text(
                    "INSERT INTO gtin_registro "
                    "(id, producto_id, gtin, estado_gtin, es_vigente, created_at) "
                    "VALUES (:id, :producto_id, :gtin, 'activo', TRUE, NOW())"
                ),
                {"id": uuid.uuid4(), "producto_id": producto_id, "gtin": gtin},
            )
            await session.commit()
        return {"id": producto_id, "sufijo": sufijo, "gtin": gtin}

    yield _crear

    async with factory() as session:
        await session.execute(
            text("DELETE FROM producto_prospectos WHERE producto_id = :id"),
            {"id": str(producto_id)},
        )
        result = await session.execute(
            text("SELECT id FROM prospectos WHERE numero_expediente LIKE :pat"),
            {"pat": f"EXP-{sufijo}%"},
        )
        prospecto_ids = [row[0] for row in result.fetchall()]
        if prospecto_ids:
            await session.execute(
                text("DELETE FROM prospectos WHERE id = ANY(:ids)"),
                {"ids": [str(i) for i in prospecto_ids]},
            )
        await session.execute(
            text("DELETE FROM gtin_registro WHERE producto_id = :id"), {"id": str(producto_id)}
        )
        await session.execute(
            text("DELETE FROM productos WHERE id = :id"), {"id": str(producto_id)}
        )
        await session.commit()
    await engine.dispose()


def _headers(token: str | None = INTERNAL_API_TOKEN) -> dict:
    return {"X-Internal-Token": token} if token is not None else {}


async def _subir_y_activar(
    auth_client: AsyncClient, sufijo: str, producto_id: uuid.UUID, version: int, tipo_audiencia: str
) -> None:
    data = {
        "numero_expediente": f"EXP-{sufijo}-{tipo_audiencia}",
        "version": str(version),
        "tipo_audiencia": tipo_audiencia,
        "producto_id": str(producto_id),
    }
    files = {"archivo": ("prospecto.pdf", PDF_VALIDO, "application/pdf")}
    subida = await auth_client.post("/api/prospectos", data=data, files=files)
    assert subida.status_code == 201
    prospecto_id = subida.json()["id"]
    activacion = await auth_client.patch(
        f"/api/prospectos/{prospecto_id}/activar", json={"producto_id": str(producto_id)}
    )
    assert activacion.status_code == 200


# ── TC1: sin header X-Internal-Token → 403 ────────────────────────────────


@pytest.mark.asyncio
async def test_resolver_sin_header_token_retorna_403(client: AsyncClient) -> None:
    response = await client.get(f"/api/internal/prospectos/by-gtin/{_gtin()}")
    assert response.status_code == 403


# ── TC2: X-Internal-Token incorrecto → 403 ────────────────────────────────


@pytest.mark.asyncio
async def test_resolver_token_incorrecto_retorna_403(client: AsyncClient) -> None:
    response = await client.get(
        f"/api/internal/prospectos/by-gtin/{_gtin()}",
        headers=_headers("token-incorrecto"),
    )
    assert response.status_code == 403


# ── TC3: formato de GTIN inválido con token correcto → 422 ────────────────


@pytest.mark.asyncio
async def test_resolver_gtin_formato_invalido_retorna_422(client: AsyncClient) -> None:
    if not INTERNAL_API_TOKEN:
        pytest.skip("INTERNAL_API_TOKEN no configurada")
    response = await client.get(
        "/api/internal/prospectos/by-gtin/12345",
        headers=_headers(),
    )
    assert response.status_code == 422


# ── TC4: GTIN inexistente → 200, error no_encontrado ──────────────────────


@pytest.mark.asyncio
async def test_resolver_gtin_inexistente_retorna_no_encontrado(client: AsyncClient) -> None:
    if not INTERNAL_API_TOKEN:
        pytest.skip("INTERNAL_API_TOKEN no configurada")
    response = await client.get(
        f"/api/internal/prospectos/by-gtin/{_gtin()}",
        headers=_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["error"] == "no_encontrado"
    assert body["producto"] is None
    assert body["prospectos"] == []
    assert body["tiene_dos_prospectos"] is False
    assert body["tipo_landing"] == "error"


# ── TC5: producto inactivo → 200, error inactivo ──────────────────────────


@pytest.mark.asyncio
async def test_resolver_producto_inactivo_retorna_error_inactivo(
    client: AsyncClient, gtin_seed
) -> None:
    seed = await gtin_seed(estado="inactivo")
    response = await client.get(
        f"/api/internal/prospectos/by-gtin/{seed['gtin']}",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["error"] == "inactivo"


# ── TC6: producto activo sin prospecto vigente → 200, error sin_prospecto ─


@pytest.mark.asyncio
async def test_resolver_sin_prospecto_vigente_retorna_error(
    client: AsyncClient, gtin_seed
) -> None:
    seed = await gtin_seed(estado="activo")
    response = await client.get(
        f"/api/internal/prospectos/by-gtin/{seed['gtin']}",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["error"] == "sin_prospecto"


# ── TC7: producto activo con un solo prospecto vigente ────────────────────


@pytest.mark.asyncio
async def test_resolver_un_prospecto_vigente_retorna_unico(
    client: AsyncClient, auth_client: AsyncClient, gtin_seed
) -> None:
    seed = await gtin_seed(estado="activo")
    await _subir_y_activar(auth_client, seed["sufijo"], seed["id"], version=1, tipo_audiencia="unico")

    response = await client.get(
        f"/api/internal/prospectos/by-gtin/{seed['gtin']}",
        headers=_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["producto"]["id"] == str(seed["id"])
    assert len(body["prospectos"]) == 1
    assert body["prospectos"][0]["tipo_audiencia"] == "unico"
    assert body["tiene_dos_prospectos"] is False
    assert body["tipo_landing"] == "unico"


# ── TC8: producto activo con dos prospectos vigentes ──────────────────────


@pytest.mark.asyncio
async def test_resolver_dos_prospectos_vigentes_retorna_selector(
    client: AsyncClient, auth_client: AsyncClient, gtin_seed
) -> None:
    seed = await gtin_seed(estado="activo")
    await _subir_y_activar(
        auth_client, seed["sufijo"], seed["id"], version=1, tipo_audiencia="publico_general"
    )
    await _subir_y_activar(
        auth_client, seed["sufijo"], seed["id"], version=1, tipo_audiencia="profesional_salud"
    )

    response = await client.get(
        f"/api/internal/prospectos/by-gtin/{seed['gtin']}",
        headers=_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["prospectos"]) == 2
    assert body["tiene_dos_prospectos"] is True
    assert body["tipo_landing"] == "selector"
    audiencias = {p["tipo_audiencia"] for p in body["prospectos"]}
    assert audiencias == {"publico_general", "profesional_salud"}
