"""
TC1-TC8: Tests de integración para los endpoints de prospectos (T11).

Patrón NullPool establecido en T7 (test_autorizacion.py). El cliente r2
(src.services.storage.r2) se mockea siguiendo el patrón de T10
(test_storage.py) para no depender de R2 real en CI.
"""

import os
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.db import get_db
from src.core.security import COOKIE_NAME
from src.main import app
from src.models.prospecto import Prospecto

DATABASE_URL = os.environ.get("DATABASE_URL", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_INITIAL_PASSWORD", "")

PDF_VALIDO = b"%PDF-1.4\n%mock prospecto de prueba\n%%EOF"
NO_PDF = b"esto no es un pdf"


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


@pytest_asyncio.fixture
async def producto_seed():
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sufijo = uuid.uuid4().hex[:8]
    producto_id = uuid.uuid4()

    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO productos "
                "(id, codigo_interno, nombre_comercial, forma_farmaceutica, "
                "presentacion_cantidad, canal, estado, tiene_prospecto, created_at, updated_at) "
                "VALUES (:id, :codigo_interno, :nombre, 'comprimidos', 'x30', "
                "'farmacia', 'activo', FALSE, NOW(), NOW())"
            ),
            {
                "id": producto_id,
                "codigo_interno": f"T11-{sufijo}",
                "nombre": f"PRODUCTO T11 {sufijo}",
            },
        )
        await session.commit()

    yield {"id": producto_id, "sufijo": sufijo}

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
            text("DELETE FROM productos WHERE id = :id"), {"id": str(producto_id)}
        )
        await session.commit()
    await engine.dispose()


def _multipart(sufijo: str, producto_id: uuid.UUID, version: int = 1, tipo_audiencia: str = "unico", contenido: bytes = PDF_VALIDO):
    data = {
        "numero_expediente": f"EXP-{sufijo}",
        "version": str(version),
        "tipo_audiencia": tipo_audiencia,
        "producto_id": str(producto_id),
    }
    files = {"archivo": ("prospecto.pdf", contenido, "application/pdf")}
    return data, files


async def _subir_prospecto(
    auth_client: AsyncClient, sufijo: str, producto_id: uuid.UUID, version: int = 1, tipo_audiencia: str = "unico"
):
    data, files = _multipart(sufijo, producto_id, version=version, tipo_audiencia=tipo_audiencia)
    return await auth_client.post("/api/prospectos", data=data, files=files)


# ── TC1: upload de PDF válido crea registro en_revision ──────────────────


@pytest.mark.asyncio
async def test_subir_prospecto_pdf_valido_crea_en_revision(
    auth_client: AsyncClient, producto_seed
) -> None:
    response = await _subir_prospecto(auth_client, producto_seed["sufijo"], producto_seed["id"])

    assert response.status_code == 201
    body = response.json()
    assert body["estado_vigencia"] == "en_revision"
    assert body["numero_expediente"] == f"EXP-{producto_seed['sufijo']}"
    assert body["url_archivo"]


# ── TC2: upload de archivo no-PDF retorna 400 ─────────────────────────────


@pytest.mark.asyncio
async def test_subir_prospecto_no_pdf_retorna_400(auth_client: AsyncClient, producto_seed) -> None:
    data, files = _multipart(producto_seed["sufijo"], producto_seed["id"], contenido=NO_PDF)
    response = await auth_client.post("/api/prospectos", data=data, files=files)

    assert response.status_code == 400


# ── TC3: producto_id inexistente retorna 404 ──────────────────────────────


@pytest.mark.asyncio
async def test_subir_prospecto_producto_inexistente_retorna_404(auth_client: AsyncClient) -> None:
    sufijo = uuid.uuid4().hex[:8]
    data, files = _multipart(sufijo, uuid.uuid4())
    response = await auth_client.post("/api/prospectos", data=data, files=files)

    assert response.status_code == 404


# ── TC4: activar sin vigente previo ───────────────────────────────────────


@pytest.mark.asyncio
async def test_activar_prospecto_sin_vigente_previo_activa(
    auth_client: AsyncClient, producto_seed
) -> None:
    subida = await _subir_prospecto(auth_client, producto_seed["sufijo"], producto_seed["id"])
    prospecto_id = subida.json()["id"]

    response = await auth_client.patch(
        f"/api/prospectos/{prospecto_id}/activar",
        json={"producto_id": str(producto_seed["id"])},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["activado"]["estado_vigencia"] == "vigente"
    assert body["reemplazado"] is None

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text("SELECT tiene_prospecto FROM productos WHERE id = :id"),
                {"id": str(producto_seed["id"])},
            )
            tiene_prospecto = result.scalar_one()
    finally:
        await engine.dispose()

    assert tiene_prospecto is True


# ── TC5: activar reemplaza vigente previo de la misma audiencia ──────────


@pytest.mark.asyncio
async def test_activar_prospecto_reemplaza_vigente_previo(
    auth_client: AsyncClient, producto_seed
) -> None:
    sufijo = producto_seed["sufijo"]
    producto_id = producto_seed["id"]

    r1 = await _subir_prospecto(auth_client, sufijo, producto_id, version=1)
    prospecto1_id = r1.json()["id"]
    await auth_client.patch(
        f"/api/prospectos/{prospecto1_id}/activar", json={"producto_id": str(producto_id)}
    )

    r2 = await _subir_prospecto(auth_client, sufijo, producto_id, version=2)
    prospecto2_id = r2.json()["id"]
    response = await auth_client.patch(
        f"/api/prospectos/{prospecto2_id}/activar", json={"producto_id": str(producto_id)}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["activado"]["id"] == prospecto2_id
    assert body["reemplazado"]["id"] == prospecto1_id
    assert body["reemplazado"]["estado_vigencia"] == "reemplazado"

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT COUNT(*) FROM producto_prospectos "
                    "WHERE producto_id = :pid AND activo = TRUE"
                ),
                {"pid": str(producto_id)},
            )
            activos = result.scalar_one()
    finally:
        await engine.dispose()

    assert activos == 1


# ── TC6: activar un prospecto ya vigente retorna 409 ──────────────────────


@pytest.mark.asyncio
async def test_activar_prospecto_ya_vigente_retorna_409(
    auth_client: AsyncClient, producto_seed
) -> None:
    subida = await _subir_prospecto(auth_client, producto_seed["sufijo"], producto_seed["id"])
    prospecto_id = subida.json()["id"]
    await auth_client.patch(
        f"/api/prospectos/{prospecto_id}/activar",
        json={"producto_id": str(producto_seed["id"])},
    )

    response = await auth_client.patch(
        f"/api/prospectos/{prospecto_id}/activar",
        json={"producto_id": str(producto_seed["id"])},
    )

    assert response.status_code == 409


# ── TC7: atomicidad — fallo a mitad no persiste ningún cambio ────────────


async def _activar_falla_a_mitad(self, producto_id, prospecto_id, tipo_audiencia):
    from src.models.producto_prospecto import ProductoProspecto

    self.session.add(
        ProductoProspecto(producto_id=producto_id, prospecto_id=prospecto_id, activo=True)
    )
    result = await self.session.execute(select(Prospecto).where(Prospecto.id == prospecto_id))
    prospecto_nuevo = result.scalar_one()
    prospecto_nuevo.estado_vigencia = "vigente"
    self.session.add(prospecto_nuevo)

    raise RuntimeError("fallo simulado a mitad de la activación")


@pytest.mark.asyncio
async def test_activar_prospecto_fallo_a_mitad_no_persiste_nada(
    auth_client: AsyncClient, producto_seed
) -> None:
    subida = await _subir_prospecto(auth_client, producto_seed["sufijo"], producto_seed["id"])
    prospecto_id = subida.json()["id"]

    with patch(
        "src.repositories.prospectos.ProspectosRepository.activar_prospecto",
        _activar_falla_a_mitad,
    ):
        with pytest.raises(RuntimeError):
            await auth_client.patch(
                f"/api/prospectos/{prospecto_id}/activar",
                json={"producto_id": str(producto_seed["id"])},
            )

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text("SELECT estado_vigencia FROM prospectos WHERE id = :id"),
                {"id": prospecto_id},
            )
            estado = result.scalar_one()

            result = await session.execute(
                text("SELECT COUNT(*) FROM producto_prospectos WHERE prospecto_id = :id"),
                {"id": prospecto_id},
            )
            asociaciones = result.scalar_one()

            result = await session.execute(
                text("SELECT tiene_prospecto FROM productos WHERE id = :id"),
                {"id": str(producto_seed["id"])},
            )
            tiene_prospecto = result.scalar_one()
    finally:
        await engine.dispose()

    assert estado == "en_revision"
    assert asociaciones == 0
    assert tiene_prospecto is False


# ── TC8: máximo un vigente por audiencia, dos audiencias en simultáneo ───


@pytest.mark.asyncio
async def test_activar_maximo_un_vigente_por_audiencia(
    auth_client: AsyncClient, producto_seed
) -> None:
    sufijo = producto_seed["sufijo"]
    producto_id = producto_seed["id"]

    r_publico = await _subir_prospecto(
        auth_client, sufijo, producto_id, version=1, tipo_audiencia="publico_general"
    )
    prospecto_publico_id = r_publico.json()["id"]
    await auth_client.patch(
        f"/api/prospectos/{prospecto_publico_id}/activar", json={"producto_id": str(producto_id)}
    )

    r_profesional = await _subir_prospecto(
        auth_client, sufijo, producto_id, version=1, tipo_audiencia="profesional_salud"
    )
    prospecto_profesional_id = r_profesional.json()["id"]
    await auth_client.patch(
        f"/api/prospectos/{prospecto_profesional_id}/activar",
        json={"producto_id": str(producto_id)},
    )

    r_publico2 = await _subir_prospecto(
        auth_client, sufijo, producto_id, version=2, tipo_audiencia="publico_general"
    )
    prospecto_publico2_id = r_publico2.json()["id"]
    response = await auth_client.patch(
        f"/api/prospectos/{prospecto_publico2_id}/activar", json={"producto_id": str(producto_id)}
    )

    assert response.status_code == 200
    assert response.json()["reemplazado"]["id"] == prospecto_publico_id

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT p.tipo_audiencia, p.estado_vigencia FROM prospectos p "
                    "JOIN producto_prospectos pp ON pp.prospecto_id = p.id "
                    "WHERE pp.producto_id = :pid AND pp.activo = TRUE"
                ),
                {"pid": str(producto_id)},
            )
            vigentes = result.fetchall()
    finally:
        await engine.dispose()

    audiencias_vigentes = {row[0] for row in vigentes}
    assert audiencias_vigentes == {"publico_general", "profesional_salud"}
    assert all(row[1] == "vigente" for row in vigentes)


# ── TC9: listado sin filtros incluye el prospecto recién creado ─────────


@pytest.mark.asyncio
async def test_listar_prospectos_sin_filtros_incluye_prospecto_creado(
    auth_client: AsyncClient, producto_seed
) -> None:
    subida = await _subir_prospecto(auth_client, producto_seed["sufijo"], producto_seed["id"])
    prospecto_id = subida.json()["id"]

    response = await auth_client.get("/api/prospectos")

    assert response.status_code == 200
    body = response.json()
    assert any(p["id"] == prospecto_id for p in body["data"])
    assert "total" in body and "page" in body and "limit" in body


# ── TC10: listado por producto_id devuelve vigentes y reemplazados ──────


@pytest.mark.asyncio
async def test_listar_prospectos_por_producto_id_incluye_vigente_y_reemplazado(
    auth_client: AsyncClient, producto_seed
) -> None:
    sufijo = producto_seed["sufijo"]
    producto_id = producto_seed["id"]

    r1 = await _subir_prospecto(auth_client, sufijo, producto_id, version=1)
    prospecto1_id = r1.json()["id"]
    await auth_client.patch(
        f"/api/prospectos/{prospecto1_id}/activar", json={"producto_id": str(producto_id)}
    )

    r2 = await _subir_prospecto(auth_client, sufijo, producto_id, version=2)
    prospecto2_id = r2.json()["id"]
    await auth_client.patch(
        f"/api/prospectos/{prospecto2_id}/activar", json={"producto_id": str(producto_id)}
    )

    response = await auth_client.get("/api/prospectos", params={"producto_id": str(producto_id)})

    assert response.status_code == 200
    body = response.json()
    ids_estado = {p["id"]: p["estado_vigencia"] for p in body["data"]}
    assert ids_estado[prospecto1_id] == "reemplazado"
    assert ids_estado[prospecto2_id] == "vigente"


# ── TC11: listado filtrado por estado_vigencia ───────────────────────────


@pytest.mark.asyncio
async def test_listar_prospectos_filtrado_por_estado_vigencia(
    auth_client: AsyncClient, producto_seed
) -> None:
    producto_id = producto_seed["id"]
    subida = await _subir_prospecto(auth_client, producto_seed["sufijo"], producto_id)
    prospecto_id = subida.json()["id"]

    response = await auth_client.get(
        "/api/prospectos",
        params={"estado_vigencia": "en_revision", "limit": 200},
    )

    assert response.status_code == 200
    body = response.json()
    assert all(p["estado_vigencia"] == "en_revision" for p in body["data"])
    assert any(p["id"] == prospecto_id for p in body["data"])


# ── TC12: download-url de un prospecto existente retorna URL firmada ────


@pytest.mark.asyncio
async def test_obtener_download_url_prospecto_existente_retorna_url(
    auth_client: AsyncClient, producto_seed, mock_r2
) -> None:
    url_esperada = "https://r2.example.com/presigned?sig=abc123"
    mock_r2.generate_presigned_url.return_value = url_esperada

    subida = await _subir_prospecto(auth_client, producto_seed["sufijo"], producto_seed["id"])
    prospecto_id = subida.json()["id"]

    response = await auth_client.get(f"/api/prospectos/{prospecto_id}/download-url")

    assert response.status_code == 200
    assert response.json()["url"] == url_esperada


# ── TC13: download-url de un prospecto inexistente retorna 404 ──────────


@pytest.mark.asyncio
async def test_obtener_download_url_prospecto_inexistente_retorna_404(
    auth_client: AsyncClient,
) -> None:
    response = await auth_client.get(f"/api/prospectos/{uuid.uuid4()}/download-url")

    assert response.status_code == 404


# ── TC14: listado y download-url sin autenticación retornan 401 ─────────


@pytest.mark.asyncio
async def test_listar_y_download_url_sin_autenticacion_retorna_401(client: AsyncClient) -> None:
    response_listar = await client.get("/api/prospectos")
    response_download = await client.get(f"/api/prospectos/{uuid.uuid4()}/download-url")

    assert response_listar.status_code == 401
    assert response_download.status_code == 401
