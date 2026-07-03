"""
TC1-TC8: Tests de integración para el script de migración de Excel (T14).

Usa un fixture .xlsx reducido (generado en memoria con openpyxl), no el
Excel real de 167 productos — más rápido y con asserts exactos.

Para correr contra la DB local de desarrollo:
    DATABASE_URL=postgresql+asyncpg://vent3:vent3dev@localhost:5433/vent3_db pytest tests/test_migracion_excel.py -v
"""

import os
import uuid

import openpyxl
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from scripts.migrar_excel import digito_verificador_gtin14, leer_bloques, migrar, normalizar

DATABASE_URL = os.environ.get("DATABASE_URL", "")

HEADERS = [
    "ID", "Código interno", "Producto", "Droga", "Potencia", "Forma Farmacéutica",
    "Presentación", "ESTADO", "Prospecto", "Estuche", "Aluminio", "PVC", "Frasco",
    "Etiqueta", "Vaso/Insreto", "Tapa",
]

CODIGOS_TPL = ["T14-S1-{s}", "T14-S2-{s}", "T14-M1-{s}", "T14-F1-{s}", "T14-L1-{s}", "MU-T14-{s}", "T14-P1-{s}"]


def _make_engine_factory():
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, factory


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


def _filas_fixture(s: str) -> list[tuple]:
    return [
        (1, f"T14-S1-{s}", "IBUPROFENO VENT3", f"Ibuprofeno {s} ", "400 mg", "Comprimidos",
         30, "A", None, "Est-1", "Alu-1", "PVC-1", None, "Etq-1", "Vaso-1", "Tapa-1"),
        (2, f"T14-S2-{s}", "IBUPROFENO VENT3 FORTE", f"Ibuprofeno {s}", "600 mg", "Comprimidos",
         20, "A", None, None, None, None, "Frasco-2", None, None, None),
        (3, f"T14-M1-{s}", "ASPIRINA COMPUESTA", f"Aspirina {s}", "500 mg", "Comprimidos",
         16, "A", None, None, None, None, None, None, None, None),
        (None, None, None, f"Vitamina C {s}", "200 mg", None, None, None, None,
         None, None, None, None, None, None),
        (4, f"T14-F1-{s}", "PARACETAMOL VENT3", f"Paracetamol {s}", "0.1", "solución oral",
         1, "A", None, "Caja-4", "N/A", "N/A", "F-46", "Etq-4", "Vaso-4", "Tapa-4"),
        (None, None, None, None, None, None, None, None, None,
         None, None, None, "F-44", None, None, None),
        (5, f"T14-L1-{s}", "AMOXICILINA LICITACION", f"Amoxicilina {s}", "500 mg", "Comprimidos",
         "licitaciín x 60", "A", None, None, None, None, None, None, None, None),
        (6, f"MU-T14-{s}", "AZYTEV TEST", f"Azitromicina {s}", "250 mg", "Comprimidos",
         6, "A", None, None, None, None, None, None, None, None),
        (7, f"T14-P1-{s}", "DICLOFENAC EN PROCESO", f"Diclofenac {s}", "50 mg", "Comprimidos",
         "en proceso", "I", None, None, None, None, None, None, None, None),
    ]


@pytest.fixture
def fixture_xlsx(tmp_path):
    sufijo = uuid.uuid4().hex[:8]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hoja1"
    ws.append(HEADERS)
    for fila in _filas_fixture(sufijo):
        ws.append(fila)
    ruta = tmp_path / "fixture.xlsx"
    wb.save(ruta)
    return ruta, sufijo


@pytest_asyncio.fixture
async def migracion(db_ok, fixture_xlsx):
    ruta, sufijo = fixture_xlsx
    wb = openpyxl.load_workbook(ruta, data_only=True)
    ws = wb["Hoja1"]
    bloques = leer_bloques(ws)

    engine, factory = _make_engine_factory()
    async with factory() as session:
        stats_1 = await migrar(session, bloques)
    async with factory() as session:
        stats_2 = await migrar(session, bloques)

    yield {"stats_1": stats_1, "stats_2": stats_2, "sufijo": sufijo, "factory": factory}

    codigos = [c.format(s=sufijo) for c in CODIGOS_TPL]
    async with factory() as session:
        await session.execute(
            text(
                "DELETE FROM gtin_registro WHERE producto_id IN "
                "(SELECT id FROM productos WHERE codigo_interno = ANY(:codigos))"
            ),
            {"codigos": codigos},
        )
        await session.execute(
            text(
                "DELETE FROM producto_materiales_packaging WHERE producto_id IN "
                "(SELECT id FROM productos WHERE codigo_interno = ANY(:codigos))"
            ),
            {"codigos": codigos},
        )
        await session.execute(
            text(
                "DELETE FROM producto_principios WHERE producto_id IN "
                "(SELECT id FROM productos WHERE codigo_interno = ANY(:codigos))"
            ),
            {"codigos": codigos},
        )
        await session.execute(
            text("DELETE FROM productos WHERE codigo_interno = ANY(:codigos)"),
            {"codigos": codigos},
        )
        await session.execute(
            text("DELETE FROM principios_activos WHERE nombre LIKE :patron"),
            {"patron": f"%{sufijo}%"},
        )
        await session.commit()
    await engine.dispose()


# ── TC1: primera ejecución crea lo esperado ───────────────────────────────────


async def test_primera_ejecucion_crea_productos_esperados(migracion):
    stats = migracion["stats_1"]
    assert stats["productos_creados"] == 6
    assert stats["productos_saltados"] == 0
    assert stats["en_proceso_ignorados"] == 1
    assert stats["principios_creados"] == 6
    assert stats["principios_reusados"] == 1


# ── TC2: segunda ejecución no duplica ─────────────────────────────────────────


async def test_segunda_ejecucion_no_duplica(migracion):
    stats = migracion["stats_2"]
    assert stats["productos_creados"] == 0
    assert stats["productos_saltados"] == 6
    assert stats["en_proceso_ignorados"] == 1
    assert stats["principios_creados"] == 0
    assert stats["principios_reusados"] == 0


# ── TC3: multi-droga genera N filas en producto_principios en orden ──────────


async def test_multidroga_genera_principios_en_orden(migracion):
    sufijo = migracion["sufijo"]
    factory = migracion["factory"]
    async with factory() as session:
        result = await session.execute(
            text(
                "SELECT pa.nombre, pp.potencia, pp.orden FROM producto_principios pp "
                "JOIN principios_activos pa ON pa.id = pp.principio_id "
                "JOIN productos p ON p.id = pp.producto_id "
                "WHERE p.codigo_interno = :codigo ORDER BY pp.orden"
            ),
            {"codigo": f"T14-M1-{sufijo}"},
        )
        filas = result.all()

    assert len(filas) == 2
    assert filas[0].nombre == f"Aspirina {sufijo}"
    assert filas[0].potencia == "500 mg"
    assert filas[0].orden == 1
    assert filas[1].nombre == f"Vitamina C {sufijo}"
    assert filas[1].potencia == "200 mg"
    assert filas[1].orden == 2


# ── TC4: "en proceso" no genera producto ──────────────────────────────────────


async def test_en_proceso_no_genera_producto(migracion):
    sufijo = migracion["sufijo"]
    factory = migracion["factory"]
    async with factory() as session:
        result = await session.execute(
            text("SELECT id FROM productos WHERE codigo_interno = :codigo"),
            {"codigo": f"T14-P1-{sufijo}"},
        )
        assert result.first() is None


# ── TC5: licitación (con typo) resuelve canal correctamente ──────────────────


async def test_licitacion_con_typo_resuelve_canal(migracion):
    sufijo = migracion["sufijo"]
    factory = migracion["factory"]
    async with factory() as session:
        result = await session.execute(
            text(
                "SELECT canal, presentacion_cantidad FROM productos WHERE codigo_interno = :codigo"
            ),
            {"codigo": f"T14-L1-{sufijo}"},
        )
        fila = result.one()

    assert fila.canal == "licitacion"
    assert fila.presentacion_cantidad == "licitacion"


# ── TC6: frasco secundario no crea un segundo packaging ──────────────────────


async def test_frasco_secundario_va_a_notas(migracion):
    sufijo = migracion["sufijo"]
    factory = migracion["factory"]
    async with factory() as session:
        result = await session.execute(
            text(
                "SELECT pmp.tipo_envase, pmp.codigo_frasco, pmp.notas FROM producto_materiales_packaging pmp "
                "JOIN productos p ON p.id = pmp.producto_id WHERE p.codigo_interno = :codigo"
            ),
            {"codigo": f"T14-F1-{sufijo}"},
        )
        filas = result.all()

    assert len(filas) == 1
    assert filas[0].tipo_envase == "frasco"
    assert filas[0].codigo_frasco == "F-46"
    assert filas[0].notas == "Frasco alternativo: F-44"


# ── TC7: cada producto migrado tiene un gtin_registro placeholder válido ─────


async def test_cada_producto_tiene_gtin_placeholder_valido(migracion):
    sufijo = migracion["sufijo"]
    factory = migracion["factory"]
    codigos = [c.format(s=sufijo) for c in CODIGOS_TPL if c != "T14-P1-{s}"]

    async with factory() as session:
        result = await session.execute(
            text(
                "SELECT p.codigo_interno, g.gtin, g.estado_gtin, g.es_vigente, "
                "g.qr_generado, g.validado_gs1 FROM gtin_registro g "
                "JOIN productos p ON p.id = g.producto_id WHERE p.codigo_interno = ANY(:codigos)"
            ),
            {"codigos": codigos},
        )
        filas = result.all()

    assert len(filas) == 6
    for fila in filas:
        assert len(fila.gtin) == 14
        assert fila.gtin.isdigit()
        assert digito_verificador_gtin14(fila.gtin[:13]) == fila.gtin[13]
        assert fila.estado_gtin == "en_desarrollo"
        assert fila.es_vigente is False
        assert fila.qr_generado is False
        assert fila.validado_gs1 is False


# ── TC8: mismo principio con distinto trimming resuelve al mismo registro ────


async def test_mismo_principio_distinto_trimming_no_duplica(migracion):
    sufijo = migracion["sufijo"]
    factory = migracion["factory"]
    nombre_esperado_normalizado = normalizar(f"Ibuprofeno {sufijo}")

    async with factory() as session:
        result = await session.execute(
            text("SELECT id FROM principios_activos WHERE nombre_normalizado = :n"),
            {"n": nombre_esperado_normalizado},
        )
        filas = result.all()
        assert len(filas) == 1
        principio_id = filas[0].id

        result = await session.execute(
            text(
                "SELECT DISTINCT pp.principio_id FROM producto_principios pp "
                "JOIN productos p ON p.id = pp.producto_id "
                "WHERE p.codigo_interno = ANY(:codigos)"
            ),
            {"codigos": [f"T14-S1-{sufijo}", f"T14-S2-{sufijo}"]},
        )
        principio_ids = {r.principio_id for r in result.all()}

    assert principio_ids == {principio_id}
