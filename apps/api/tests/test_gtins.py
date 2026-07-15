"""
Tests de integración para PATCH /api/gtins/{id} (gap de T25/T26).

Patrón NullPool establecido en T7 (test_autorizacion.py): cada request
usa una conexión nueva para evitar "Future attached to different loop"
con pytest-asyncio. Mismo fixture shape que test_productos.py.
"""

import os
import uuid
from collections.abc import AsyncGenerator

import bcrypt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.db import get_db
from src.core.security import COOKIE_NAME, crear_access_token
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
async def usuario_con_rol(db_ok: None):
    """Crea un usuario de prueba con el rol indicado y devuelve un cliente ya autenticado.

    A diferencia de auth_client (que loguea al admin real vía /api/auth/login), acá se
    inserta el usuario directo por SQL y se firma el JWT con crear_access_token — mismo
    patrón que test_autorizacion.py::test_endpoint_admin_usuario_inactivo_retorna_401 —
    porque no existe (ni debería, es MVP de un solo admin) un flujo de alta de usuarios
    editor/lector vía API todavía.
    """
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    emails_creados: list[str] = []

    async def _crear(rol: str) -> AsyncClient:
        email = f"test_{rol}_{uuid.uuid4().hex[:8]}@vent3.test"
        password_hash = bcrypt.hashpw(b"test-pass-xyz", bcrypt.gensalt(rounds=4)).decode()
        async with factory() as session:
            await session.execute(
                text(
                    "INSERT INTO usuarios (id, email, nombre, password_hash, rol, activo, intentos_fallidos, created_at) "
                    "VALUES (gen_random_uuid(), :email, :nombre, :hash, :rol, TRUE, 0, NOW())"
                ),
                {"email": email, "nombre": f"Test {rol}", "hash": password_hash, "rol": rol},
            )
            await session.commit()

        token = crear_access_token({"sub": email})
        client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        client.cookies.set(COOKIE_NAME, token)
        emails_creados.append(email)
        return client

    try:
        yield _crear
    finally:
        # No se borra el usuario: los PATCH del test dejan filas en audit_log
        # (append-only, FK a usuarios.id — CLAUDE.md prohíbe DELETE en tablas
        # de negocio) que quedarían huérfanas. Se aplica el mismo soft-delete
        # que usa el resto del proyecto (campo `activo`).
        async with factory() as session:
            for email in emails_creados:
                await session.execute(
                    text("UPDATE usuarios SET activo = FALSE WHERE email = :email"),
                    {"email": email},
                )
            await session.commit()
        await engine.dispose()


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


@pytest_asyncio.fixture
async def gtin_seed_2():
    """Segundo producto+GTIN independiente, para probar conflictos de unicidad."""
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
                "codigo_interno": f"T25-B-{sufijo}",
                "nombre_comercial": f"PRODUCTO GTIN TEST DOS {sufijo}",
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

    async with factory() as session:
        await session.execute(
            text("DELETE FROM gtin_registro WHERE id = :id"), {"id": gtin_id}
        )
        await session.execute(
            text("DELETE FROM productos WHERE id = :id"), {"id": producto_id}
        )
        await session.commit()
    await engine.dispose()


@pytest_asyncio.fixture
async def producto_dos_gtins():
    """Un producto con dos GTIN: uno vigente y otro no — para probar el reemplazo automático."""
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sufijo = uuid.uuid4().hex[:8]
    producto_id = uuid.uuid4()
    gtin_vigente_id = uuid.uuid4()
    gtin_nuevo_id = uuid.uuid4()
    gtin_vigente_numero = f"029{uuid.uuid4().int % 10**11:011d}"
    gtin_nuevo_numero = f"029{uuid.uuid4().int % 10**11:011d}"

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
                "codigo_interno": f"T25-V-{sufijo}",
                "nombre_comercial": f"PRODUCTO DOS GTIN TEST {sufijo}",
            },
        )
        await session.execute(
            text(
                "INSERT INTO gtin_registro "
                "(id, producto_id, gtin, estado_gtin, es_vigente, url_digital_link, "
                "qr_generado, validado_gs1, created_at) "
                "VALUES "
                "(:id_v, :producto_id, :gtin_v, 'activo', TRUE, NULL, FALSE, FALSE, NOW()), "
                "(:id_n, :producto_id, :gtin_n, 'en_desarrollo', FALSE, NULL, FALSE, FALSE, NOW())"
            ),
            {
                "id_v": gtin_vigente_id,
                "gtin_v": gtin_vigente_numero,
                "id_n": gtin_nuevo_id,
                "gtin_n": gtin_nuevo_numero,
                "producto_id": producto_id,
            },
        )
        await session.commit()

    yield {
        "producto_id": producto_id,
        "gtin_vigente_id": gtin_vigente_id,
        "gtin_nuevo_id": gtin_nuevo_id,
    }

    async with factory() as session:
        await session.execute(
            text("DELETE FROM gtin_registro WHERE producto_id = :id"), {"id": producto_id}
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


# ── TC1b: GET /api/productos/{id} expone gtin_registros ───────────────────


@pytest.mark.asyncio
async def test_obtener_producto_expone_gtin_registros_asociados(
    auth_client: AsyncClient, gtin_seed
) -> None:
    response = await auth_client.get(f"/api/productos/{gtin_seed['producto_id']}")

    assert response.status_code == 200
    body = response.json()
    assert len(body["gtin_registros"]) == 1
    assert body["gtin_registros"][0]["gtin"] == gtin_seed["gtin"]
    assert body["gtin_registros"][0]["qr_generado"] is False


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


# ── TC5: PATCH corrige el número de gtin mientras qr_generado=False ───────


@pytest.mark.asyncio
async def test_actualizar_gtin_corrige_numero_antes_de_generar_qr_y_audita(
    auth_client: AsyncClient, gtin_seed
) -> None:
    gtin_id = gtin_seed["gtin_id"]
    gtin_real = f"779{uuid.uuid4().int % 10**11:011d}"

    response = await auth_client.patch(
        f"/api/gtins/{gtin_id}", json={"gtin": gtin_real}
    )

    assert response.status_code == 200
    assert response.json()["gtin"] == gtin_real

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT campo_modificado, valor_anterior, valor_nuevo FROM audit_log "
                    "WHERE registro_id = :id AND tabla_afectada = 'gtin_registro' "
                    "AND campo_modificado = 'gtin'"
                ),
                {"id": str(gtin_id)},
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    assert len(rows) == 1
    assert rows[0][1] == gtin_seed["gtin"]
    assert rows[0][2] == gtin_real


# ── TC6: PATCH rechaza modificar el gtin si el QR ya fue generado ─────────


@pytest.mark.asyncio
async def test_actualizar_gtin_con_qr_generado_rechaza_cambio_de_numero(
    auth_client: AsyncClient, gtin_seed
) -> None:
    gtin_id = gtin_seed["gtin_id"]

    # Primero se marca qr_generado=True (flujo real de T25).
    marcar = await auth_client.patch(f"/api/gtins/{gtin_id}", json={"qr_generado": True})
    assert marcar.status_code == 200

    otro_numero = f"779{uuid.uuid4().int % 10**11:011d}"
    response = await auth_client.patch(f"/api/gtins/{gtin_id}", json={"gtin": otro_numero})

    assert response.status_code == 409

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text("SELECT gtin FROM gtin_registro WHERE id = :id"), {"id": str(gtin_id)}
            )
            gtin_actual = result.scalar_one()
    finally:
        await engine.dispose()

    assert gtin_actual == gtin_seed["gtin"]


# ── TC7: PATCH rechaza gtin duplicado de otro producto ─────────────────────


@pytest.mark.asyncio
async def test_actualizar_gtin_duplicado_retorna_409(
    auth_client: AsyncClient, gtin_seed, gtin_seed_2
) -> None:
    response = await auth_client.patch(
        f"/api/gtins/{gtin_seed['gtin_id']}", json={"gtin": gtin_seed_2["gtin"]}
    )
    assert response.status_code == 409


# ── TC8: PATCH rechaza formato de gtin inválido ────────────────────────────


@pytest.mark.asyncio
async def test_actualizar_gtin_formato_invalido_retorna_422(
    auth_client: AsyncClient, gtin_seed
) -> None:
    response = await auth_client.patch(
        f"/api/gtins/{gtin_seed['gtin_id']}", json={"gtin": "no-es-un-gtin"}
    )
    assert response.status_code == 422


# ── TC9: PATCH es_vigente=true reemplaza automáticamente al anterior ──────


@pytest.mark.asyncio
async def test_actualizar_gtin_marca_vigente_reemplaza_al_anterior_y_audita(
    auth_client: AsyncClient, producto_dos_gtins
) -> None:
    gtin_nuevo_id = producto_dos_gtins["gtin_nuevo_id"]
    gtin_vigente_id = producto_dos_gtins["gtin_vigente_id"]

    response = await auth_client.patch(
        f"/api/gtins/{gtin_nuevo_id}", json={"es_vigente": True}
    )

    assert response.status_code == 200
    assert response.json()["es_vigente"] is True

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text("SELECT id, es_vigente FROM gtin_registro WHERE producto_id = :id"),
                {"id": str(producto_dos_gtins["producto_id"])},
            )
            estados = {str(r[0]): r[1] for r in result.fetchall()}

            audit_result = await session.execute(
                text(
                    "SELECT registro_id, valor_anterior, valor_nuevo FROM audit_log "
                    "WHERE tabla_afectada = 'gtin_registro' AND campo_modificado = 'es_vigente' "
                    "AND registro_id = ANY(:ids)"
                ),
                {"ids": [str(gtin_nuevo_id), str(gtin_vigente_id)]},
            )
            audit_rows = {str(r[0]): (r[1], r[2]) for r in audit_result.fetchall()}
    finally:
        await engine.dispose()

    assert estados[str(gtin_nuevo_id)] is True
    assert estados[str(gtin_vigente_id)] is False
    assert audit_rows[str(gtin_nuevo_id)] == ("False", "True")
    assert audit_rows[str(gtin_vigente_id)] == ("True", "False")


# ── TC10: PATCH es_vigente=true sin conflicto no toca otras filas ─────────


@pytest.mark.asyncio
async def test_actualizar_gtin_marca_vigente_sin_conflicto_no_afecta_otras_filas(
    auth_client: AsyncClient, gtin_seed
) -> None:
    response = await auth_client.patch(
        f"/api/gtins/{gtin_seed['gtin_id']}", json={"es_vigente": True}
    )
    assert response.status_code == 200
    assert response.json()["es_vigente"] is True


# ── TC11: rol lector no tiene acceso al endpoint ──────────────────────────


@pytest.mark.asyncio
async def test_actualizar_gtin_rol_lector_retorna_403(
    usuario_con_rol, gtin_seed
) -> None:
    lector = await usuario_con_rol("lector")
    response = await lector.patch(
        f"/api/gtins/{gtin_seed['gtin_id']}", json={"validado_gs1": True}
    )
    assert response.status_code == 403
    await lector.aclose()


# ── TC12: editor puede cargar gtin + marcar qr_generado por primera vez ───


@pytest.mark.asyncio
async def test_actualizar_gtin_rol_editor_carga_inicial_permitida(
    usuario_con_rol, gtin_seed
) -> None:
    editor = await usuario_con_rol("editor")
    url = f"https://www.vent3.com.ar/01/{gtin_seed['gtin']}"

    response = await editor.patch(
        f"/api/gtins/{gtin_seed['gtin_id']}",
        json={"url_digital_link": url, "qr_generado": True},
    )

    assert response.status_code == 200
    assert response.json()["qr_generado"] is True
    await editor.aclose()


# ── TC13: editor no puede desmarcar qr_generado ya generado ───────────────


@pytest.mark.asyncio
async def test_actualizar_gtin_rol_editor_no_puede_desmarcar_qr_generado(
    usuario_con_rol, gtin_seed
) -> None:
    editor = await usuario_con_rol("editor")
    gtin_id = gtin_seed["gtin_id"]

    marcar = await editor.patch(f"/api/gtins/{gtin_id}", json={"qr_generado": True})
    assert marcar.status_code == 200

    response = await editor.patch(f"/api/gtins/{gtin_id}", json={"qr_generado": False})
    assert response.status_code == 403

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text("SELECT qr_generado FROM gtin_registro WHERE id = :id"),
                {"id": str(gtin_id)},
            )
            qr_generado_actual = result.scalar_one()
    finally:
        await engine.dispose()

    assert qr_generado_actual is True
    await editor.aclose()


# ── TC14: editor no puede modificar url_digital_link con qr ya generado ───


@pytest.mark.asyncio
async def test_actualizar_gtin_rol_editor_no_puede_modificar_url_con_qr_generado(
    usuario_con_rol, gtin_seed
) -> None:
    editor = await usuario_con_rol("editor")
    gtin_id = gtin_seed["gtin_id"]

    marcar = await editor.patch(f"/api/gtins/{gtin_id}", json={"qr_generado": True})
    assert marcar.status_code == 200

    response = await editor.patch(
        f"/api/gtins/{gtin_id}",
        json={"url_digital_link": "https://www.vent3.com.ar/01/otra-url"},
    )
    assert response.status_code == 403
    await editor.aclose()


# ── TC15: admin sí puede desmarcar qr_generado (excepción exclusiva de admin) ──


@pytest.mark.asyncio
async def test_actualizar_gtin_admin_puede_desmarcar_qr_generado(
    auth_client: AsyncClient, gtin_seed
) -> None:
    gtin_id = gtin_seed["gtin_id"]

    marcar = await auth_client.patch(f"/api/gtins/{gtin_id}", json={"qr_generado": True})
    assert marcar.status_code == 200

    response = await auth_client.patch(f"/api/gtins/{gtin_id}", json={"qr_generado": False})
    assert response.status_code == 200
    assert response.json()["qr_generado"] is False
