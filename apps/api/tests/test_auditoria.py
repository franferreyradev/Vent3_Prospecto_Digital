"""
TC1-TC6: Tests de integración para el servicio de auditoría (T8).
Requieren la DB de test configurada.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.repositories.audit import AuditRepository
from src.services.auditoria import AuditoriaService

DATABASE_URL = os.environ.get("DATABASE_URL", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@test.com")


def _make_engine():
    return create_async_engine(DATABASE_URL, echo=False)


@pytest_asyncio.fixture
async def db_session():
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL no configurada")

    engine = _make_engine()
    try:
        connection = await engine.connect()
    except Exception as e:
        await engine.dispose()
        pytest.skip(f"DB no accesible: {e}")

    trans = await connection.begin()
    session = AsyncSession(connection, expire_on_commit=False)

    yield session

    await session.close()
    await trans.rollback()
    await connection.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def admin_id(db_session: AsyncSession):
    result = await db_session.execute(
        text("SELECT id FROM usuarios WHERE email = :email"),
        {"email": ADMIN_EMAIL},
    )
    row = result.fetchone()
    if row is None:
        pytest.skip(f"Usuario {ADMIN_EMAIL} no encontrado en DB de test")
    return row[0]


# ── TC1: registrar_cambio crea registro correcto ──────────────────────────────


@pytest.mark.asyncio
async def test_registrar_cambio_crea_registro_en_audit_log(db_session: AsyncSession, admin_id) -> None:
    registro_id = uuid.uuid4()
    service = AuditoriaService(db_session)

    await service.registrar_cambio(
        tabla="productos",
        registro_id=registro_id,
        accion="UPDATE",
        usuario_id=admin_id,
        campo="estado",
        valor_anterior="borrador",
        valor_nuevo="activo",
    )

    result = await db_session.execute(
        text(
            "SELECT tabla_afectada, accion, campo_modificado, valor_anterior, valor_nuevo, usuario_id "
            "FROM audit_log WHERE registro_id = :rid"
        ),
        {"rid": str(registro_id)},
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == "productos"
    assert row[1] == "UPDATE"
    assert row[2] == "estado"
    assert row[3] == "borrador"
    assert row[4] == "activo"
    assert str(row[5]) == str(admin_id)


# ── TC2: valores no-string se convierten a string ────────────────────────────


@pytest.mark.asyncio
async def test_registrar_cambio_convierte_valores_a_string(db_session: AsyncSession, admin_id) -> None:
    registro_id = uuid.uuid4()
    service = AuditoriaService(db_session)

    await service.registrar_cambio(
        tabla="productos",
        registro_id=registro_id,
        accion="UPDATE",
        usuario_id=admin_id,
        campo="activo",
        valor_anterior=True,
        valor_nuevo=42,
    )

    result = await db_session.execute(
        text("SELECT valor_anterior, valor_nuevo FROM audit_log WHERE registro_id = :rid"),
        {"rid": str(registro_id)},
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == "True"
    assert row[1] == "42"


# ── TC3: wrapper registrar_activacion_prospecto ───────────────────────────────


@pytest.mark.asyncio
async def test_registrar_activacion_prospecto_crea_registro_correcto(db_session: AsyncSession, admin_id) -> None:
    prospecto_id = uuid.uuid4()
    service = AuditoriaService(db_session)

    await service.registrar_activacion_prospecto(
        prospecto_id=prospecto_id,
        usuario_id=admin_id,
        estado_anterior="en_revision",
    )

    result = await db_session.execute(
        text(
            "SELECT tabla_afectada, accion, campo_modificado, valor_anterior, valor_nuevo "
            "FROM audit_log WHERE registro_id = :rid"
        ),
        {"rid": str(prospecto_id)},
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == "prospectos"
    assert row[1] == "UPDATE"
    assert row[2] == "estado_vigencia"
    assert row[3] == "en_revision"
    assert row[4] == "vigente"


@pytest.mark.asyncio
async def test_registrar_reemplazo_prospecto_crea_registro_correcto(db_session: AsyncSession, admin_id) -> None:
    prospecto_id = uuid.uuid4()
    service = AuditoriaService(db_session)

    await service.registrar_reemplazo_prospecto(
        prospecto_id=prospecto_id,
        usuario_id=admin_id,
    )

    result = await db_session.execute(
        text(
            "SELECT tabla_afectada, accion, campo_modificado, valor_anterior, valor_nuevo "
            "FROM audit_log WHERE registro_id = :rid"
        ),
        {"rid": str(prospecto_id)},
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == "prospectos"
    assert row[1] == "UPDATE"
    assert row[2] == "estado_vigencia"
    assert row[3] == "vigente"
    assert row[4] == "reemplazado"


# ── TC4: wrapper registrar_cambio_estado_producto ────────────────────────────


@pytest.mark.asyncio
async def test_registrar_cambio_estado_producto_crea_registro_correcto(db_session: AsyncSession, admin_id) -> None:
    producto_id = uuid.uuid4()
    service = AuditoriaService(db_session)

    await service.registrar_cambio_estado_producto(
        producto_id=producto_id,
        estado_anterior="borrador",
        estado_nuevo="activo",
        usuario_id=admin_id,
    )

    result = await db_session.execute(
        text(
            "SELECT tabla_afectada, accion, campo_modificado, valor_anterior, valor_nuevo "
            "FROM audit_log WHERE registro_id = :rid"
        ),
        {"rid": str(producto_id)},
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == "productos"
    assert row[1] == "UPDATE"
    assert row[2] == "estado"
    assert row[3] == "borrador"
    assert row[4] == "activo"


# ── TC5: audit_log es inmutable a nivel DB ────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_log_inmutable_update_directo_lanza_excepcion(db_session: AsyncSession, admin_id) -> None:
    registro_id = uuid.uuid4()

    # Insertar un registro para tener algo que intentar modificar
    await db_session.execute(
        text(
            "INSERT INTO audit_log (id, tabla_afectada, registro_id, accion, usuario_id) "
            "VALUES (gen_random_uuid(), 'test_tabla_tc5', :rid, 'INSERT', :uid)"
        ),
        {"rid": str(registro_id), "uid": str(admin_id)},
    )
    await db_session.flush()

    # El trigger BEFORE UPDATE FOR EACH ROW debe lanzar excepción.
    # Usamos begin_nested() (SAVEPOINT) para no abortar la transacción exterior.
    excepcion = None
    try:
        async with db_session.begin_nested():
            await db_session.execute(
                text("UPDATE audit_log SET accion = 'DELETE' WHERE tabla_afectada = 'test_tabla_tc5'")
            )
    except Exception as e:
        excepcion = e

    assert excepcion is not None, "El trigger trg_audit_inmutable debería haber lanzado excepción"
    assert "inmutable" in str(excepcion).lower()


# ── TC6: get_filtrado con filtros múltiples ───────────────────────────────────


@pytest.mark.asyncio
async def test_get_filtrado_con_filtros_multiples(db_session: AsyncSession, admin_id) -> None:
    service = AuditoriaService(db_session)
    repo = AuditRepository(db_session)

    id_productos = [uuid.uuid4() for _ in range(2)]
    id_prospecto = uuid.uuid4()

    for rid in id_productos:
        await service.registrar_cambio(
            tabla="productos",
            registro_id=rid,
            accion="INSERT",
            usuario_id=admin_id,
        )
    await service.registrar_cambio(
        tabla="prospectos",
        registro_id=id_prospecto,
        accion="INSERT",
        usuario_id=admin_id,
    )

    # Filtrar por tabla='productos' (solo registros de esta sesión de test)
    logs_productos, total_p = await repo.get_filtrado(tabla="productos", registro_id=id_productos[0])
    assert total_p == 1

    logs_prospectos, total_pr = await repo.get_filtrado(tabla="prospectos", registro_id=id_prospecto)
    assert total_pr == 1

    # Rango en el pasado excluye todos los registros recién insertados
    hace_dos_horas = datetime.now(timezone.utc) - timedelta(hours=2)
    hace_una_hora = datetime.now(timezone.utc) - timedelta(hours=1)
    _, total_vacio = await repo.get_filtrado(
        desde=hace_dos_horas,
        hasta=hace_una_hora,
    )
    assert total_vacio == 0
