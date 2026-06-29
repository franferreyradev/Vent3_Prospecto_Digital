"""
TC1-TC7: Verificación del schema PostgreSQL aplicado por las migraciones Alembic de T3.

Para correr contra la DB local de desarrollo:
    DATABASE_URL=postgresql+asyncpg://vent3:vent3dev@localhost:5433/vent3_db pytest tests/test_schema.py -v
"""

import asyncio
import os

import asyncpg
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")

TABLES_ESPERADAS = {
    "usuarios",
    "productos",
    "principios_activos",
    "producto_principios",
    "prospectos",
    "producto_prospectos",
    "gtin_registro",
    "audit_log",
    "producto_materiales_packaging",
}

ENUMS_ESPERADOS = {
    "canal_enum",
    "estado_producto_enum",
    "estado_vigencia_enum",
    "tipo_audiencia_enum",
    "estado_gtin_enum",
    "rol_usuario_enum",
    "accion_audit_enum",
    "tipo_envase_enum",
}


def _asyncpg_dsn(url: str) -> str:
    """Convierte URL de SQLAlchemy a DSN compatible con asyncpg."""
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgres://", "postgresql://")
    return url


@pytest.fixture
async def conn():
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL no configurada")

    dsn = _asyncpg_dsn(DATABASE_URL)
    try:
        connection = await asyncpg.connect(dsn)
    except Exception as e:
        pytest.skip(f"DB no accesible: {e}")

    yield connection
    await connection.close()


# ─── TC1: Las 9 tablas existen ──────────────────────────────────────────────

async def test_tablas_existen(conn):
    rows = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
    )
    tablas = {r["tablename"] for r in rows}
    assert TABLES_ESPERADAS.issubset(tablas), (
        f"Tablas faltantes: {TABLES_ESPERADAS - tablas}"
    )


# ─── TC2: Los 8 ENUMs existen ───────────────────────────────────────────────

async def test_enums_existen(conn):
    rows = await conn.fetch(
        "SELECT typname FROM pg_type WHERE typtype = 'e';"
    )
    enums = {r["typname"] for r in rows}
    assert ENUMS_ESPERADOS.issubset(enums), (
        f"ENUMs faltantes: {ENUMS_ESPERADOS - enums}"
    )


# ─── TC3: Trigger updated_at en productos ───────────────────────────────────

async def test_trigger_updated_at_productos(conn):
    prod_id = await conn.fetchval("""
        INSERT INTO productos (nombre_comercial, forma_farmaceutica, presentacion_cantidad)
        VALUES ('Test TC3', 'Comprimido', '30 comp')
        RETURNING id;
    """)
    assert prod_id is not None

    try:
        updated_at_antes = await conn.fetchval(
            "SELECT updated_at FROM productos WHERE id = $1;", prod_id
        )

        await asyncio.sleep(0.05)

        await conn.execute(
            "UPDATE productos SET nombre_comercial = 'Test TC3 updated' WHERE id = $1;",
            prod_id,
        )

        updated_at_despues = await conn.fetchval(
            "SELECT updated_at FROM productos WHERE id = $1;", prod_id
        )

        assert updated_at_despues > updated_at_antes, (
            "El trigger updated_at no actualizó el timestamp"
        )
    finally:
        await conn.execute("DELETE FROM productos WHERE id = $1;", prod_id)


# ─── TC4: Inmutabilidad de audit_log ────────────────────────────────────────

async def test_audit_log_inmutable(conn):
    import bcrypt as _bcrypt

    test_hash = _bcrypt.hashpw(b"tc4test", _bcrypt.gensalt(rounds=4)).decode("utf-8")

    user_id = await conn.fetchval("""
        INSERT INTO usuarios (email, nombre, password_hash, rol)
        VALUES ('tc4_test@test.com', 'TC4 Test', $1, 'lector')
        RETURNING id;
    """, test_hash)
    assert user_id is not None

    try:
        log_id = await conn.fetchval("""
            INSERT INTO audit_log (tabla_afectada, registro_id, accion, usuario_id)
            VALUES ('productos', gen_random_uuid(), 'INSERT', $1)
            RETURNING id;
        """, user_id)
        assert log_id is not None

        # UPDATE debe fallar con la excepción del trigger
        with pytest.raises(asyncpg.exceptions.RaiseError) as exc_info:
            await conn.execute(
                "UPDATE audit_log SET tabla_afectada = 'test' WHERE id = $1;", log_id
            )
        assert "audit_log es inmutable" in str(exc_info.value)

        # DELETE también debe fallar con la excepción del trigger
        with pytest.raises(asyncpg.exceptions.RaiseError) as exc_info:
            await conn.execute(
                "DELETE FROM audit_log WHERE id = $1;", log_id
            )
        assert "audit_log es inmutable" in str(exc_info.value)

        # Limpiar: TRUNCATE no activa triggers BEFORE UPDATE/DELETE
        await conn.execute("TRUNCATE audit_log RESTART IDENTITY CASCADE;")
    finally:
        await conn.execute("DELETE FROM usuarios WHERE email = 'tc4_test@test.com';")


# ─── TC5: Trigger normalización en principios_activos ───────────────────────

async def test_trigger_normalizacion_principio_activo(conn):
    principio_id = await conn.fetchval("""
        INSERT INTO principios_activos (nombre, nombre_normalizado)
        VALUES ('Ácido Acetilsalicílico', 'placeholder')
        RETURNING id;
    """)
    assert principio_id is not None

    try:
        nombre_norm = await conn.fetchval(
            "SELECT nombre_normalizado FROM principios_activos WHERE id = $1;",
            principio_id,
        )
        assert nombre_norm == "acido acetilsalicilico", (
            f"nombre_normalizado esperado 'acido acetilsalicilico', obtenido '{nombre_norm}'"
        )
    finally:
        await conn.execute("DELETE FROM principios_activos WHERE id = $1;", principio_id)


# ─── TC6: CHECK constraint GTIN ─────────────────────────────────────────────

async def test_check_constraint_gtin(conn):
    prod_id = await conn.fetchval("""
        INSERT INTO productos (nombre_comercial, forma_farmaceutica, presentacion_cantidad)
        VALUES ('Test TC6', 'Comprimido', '10 comp')
        RETURNING id;
    """)
    assert prod_id is not None

    try:
        # GTIN inválido — debe fallar con CheckViolationError
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await conn.execute("""
                INSERT INTO gtin_registro (producto_id, gtin)
                VALUES ($1, '123');
            """, prod_id)

        # GTIN válido (14 dígitos) — debe funcionar
        gtin_id = await conn.fetchval("""
            INSERT INTO gtin_registro (producto_id, gtin)
            VALUES ($1, '07791234567890')
            RETURNING id;
        """, prod_id)
        assert gtin_id is not None

        await conn.execute("DELETE FROM gtin_registro WHERE id = $1;", gtin_id)
    finally:
        await conn.execute("DELETE FROM productos WHERE id = $1;", prod_id)


# ─── TC7: Usuario admin existe ──────────────────────────────────────────────

async def test_usuario_admin_existe(conn):
    rows = await conn.fetch(
        "SELECT email, activo, rol FROM usuarios WHERE rol = 'admin';"
    )
    assert len(rows) >= 1, "No se encontró ningún usuario con rol='admin'"
    admin = rows[0]
    assert admin["activo"] is True, "El usuario admin está inactivo"
    assert admin["rol"] == "admin"
