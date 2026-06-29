"""
TC1-TC6: Tests de integración para los repositorios de T4.

Para correr contra la DB local de desarrollo:
    DATABASE_URL=postgresql+asyncpg://vent3:vent3dev@localhost:5433/vent3_db pytest tests/test_repositorios.py -v
"""

import os
import uuid

import bcrypt
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.models.gtin_registro import GtinRegistro
from src.models.principio_activo import PrincipioActivo
from src.models.producto import Producto
from src.models.producto_principio import ProductoPrincipio
from src.models.prospecto import Prospecto
from src.models.usuario import Usuario
from src.repositories.audit import AuditRepository
from src.repositories.productos import ProductosRepository
from src.repositories.resolver import ResolverRepository
from src.repositories.usuarios import UsuariosRepository

DATABASE_URL = os.environ.get("DATABASE_URL", "")


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


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()


def _make_usuario(**kwargs) -> Usuario:
    defaults = dict(
        email=f"test_{uuid.uuid4().hex[:8]}@test.com",
        nombre="Test User",
        password_hash=_hash("password123"),
        rol="lector",
    )
    defaults.update(kwargs)
    return Usuario(**defaults)


def _make_producto(**kwargs) -> Producto:
    defaults = dict(
        nombre_comercial=f"Producto Test {uuid.uuid4().hex[:6]}",
        forma_farmaceutica="Comprimido",
        presentacion_cantidad="30 comp",
    )
    defaults.update(kwargs)
    return Producto(**defaults)


# ─── TC1: BaseRepository.create() y get_by_id() ─────────────────────────────


async def test_base_create_y_get_by_id(db_session: AsyncSession):
    repo = ProductosRepository(db_session)
    principio = PrincipioActivo(nombre="Amoxicilina TC1", nombre_normalizado="placeholder")
    db_session.add(principio)
    await db_session.flush()
    # Refresh para obtener nombre_normalizado generado por el trigger de DB
    await db_session.refresh(principio)

    from src.repositories.base import BaseRepository

    class PrincipioRepo(BaseRepository[PrincipioActivo]):
        pass

    principio_repo = PrincipioRepo(db_session, PrincipioActivo)
    encontrado = await principio_repo.get_by_id(principio.id)

    assert encontrado is not None
    assert encontrado.nombre == "Amoxicilina TC1"
    # El trigger normalizó el nombre_normalizado
    assert encontrado.nombre_normalizado == "amoxicilina tc1"


# ─── TC2: ProductosRepository.get_all_filtrado() ─────────────────────────────


async def test_get_all_filtrado(db_session: AsyncSession):
    repo = ProductosRepository(db_session)

    prod1 = _make_producto(nombre_comercial="Amoxidal TC2 A", estado="activo")
    prod2 = _make_producto(nombre_comercial="Amoxidal TC2 B", estado="activo")
    prod3 = _make_producto(nombre_comercial="Otro TC2 C", estado="inactivo")
    db_session.add_all([prod1, prod2, prod3])
    await db_session.flush()

    activos, total_activos = await repo.get_all_filtrado(estado="activo")
    assert total_activos >= 2

    inactivos, total_inactivos = await repo.get_all_filtrado(estado="inactivo")
    assert total_inactivos >= 1

    buscados, total_busqueda = await repo.get_all_filtrado(search="Amoxidal TC2")
    assert total_busqueda >= 2


# ─── TC3: ProductosRepository.get_detalle_completo() ─────────────────────────


async def test_get_detalle_completo(db_session: AsyncSession):
    repo = ProductosRepository(db_session)

    producto = _make_producto(nombre_comercial="Producto Detalle TC3")
    db_session.add(producto)
    await db_session.flush()

    p1 = PrincipioActivo(nombre="Ibuprofeno TC3 A", nombre_normalizado="placeholder")
    p2 = PrincipioActivo(nombre="Ibuprofeno TC3 B", nombre_normalizado="placeholder")
    db_session.add_all([p1, p2])
    await db_session.flush()

    pp1 = ProductoPrincipio(
        producto_id=producto.id, principio_id=p1.id, potencia="400mg", orden=1
    )
    pp2 = ProductoPrincipio(
        producto_id=producto.id, principio_id=p2.id, potencia="600mg", orden=2
    )
    db_session.add_all([pp1, pp2])
    await db_session.flush()

    detalle = await repo.get_detalle_completo(producto.id)

    assert detalle is not None
    assert detalle.nombre_comercial == "Producto Detalle TC3"
    assert len(detalle.principios) == 2


# ─── TC4: ResolverRepository.resolver_gtin() ─────────────────────────────────


async def test_resolver_gtin_no_encontrado(db_session: AsyncSession):
    repo = ResolverRepository(db_session)
    result = await repo.resolver_gtin("99999999999999")
    assert result == {"error": "no_encontrado"}


async def test_resolver_gtin_producto_inactivo(db_session: AsyncSession):
    repo = ResolverRepository(db_session)

    producto = _make_producto(estado="inactivo")
    db_session.add(producto)
    await db_session.flush()

    gtin = GtinRegistro(
        producto_id=producto.id,
        gtin=f"{uuid.uuid4().int % 10**14:014d}",
        es_vigente=True,
    )
    db_session.add(gtin)
    await db_session.flush()

    result = await repo.resolver_gtin(gtin.gtin)
    assert result == {"error": "inactivo"}


async def test_resolver_gtin_sin_prospecto(db_session: AsyncSession):
    repo = ResolverRepository(db_session)

    producto = _make_producto(estado="activo")
    db_session.add(producto)
    await db_session.flush()

    gtin = GtinRegistro(
        producto_id=producto.id,
        gtin=f"{uuid.uuid4().int % 10**14:014d}",
        es_vigente=True,
    )
    db_session.add(gtin)
    await db_session.flush()

    result = await repo.resolver_gtin(gtin.gtin)
    assert result == {"error": "sin_prospecto"}


async def test_resolver_gtin_con_prospecto(db_session: AsyncSession):
    from src.models.producto_prospecto import ProductoProspecto
    from src.repositories.prospectos import ProspectosRepository

    repo = ResolverRepository(db_session)

    usuario = _make_usuario()
    db_session.add(usuario)
    await db_session.flush()

    producto = _make_producto(estado="activo", tiene_prospecto=True)
    db_session.add(producto)
    await db_session.flush()

    prospecto = Prospecto(
        numero_expediente="EXP-TC4D",
        version=1,
        tipo_audiencia="unico",
        url_archivo="https://r2.example.com/test.pdf",
        nombre_archivo="test.pdf",
        estado_vigencia="vigente",
        subido_por=usuario.id,
    )
    db_session.add(prospecto)
    await db_session.flush()

    asociacion = ProductoProspecto(
        producto_id=producto.id, prospecto_id=prospecto.id, activo=True
    )
    db_session.add(asociacion)

    gtin = GtinRegistro(
        producto_id=producto.id,
        gtin=f"{uuid.uuid4().int % 10**14:014d}",
        es_vigente=True,
    )
    db_session.add(gtin)
    await db_session.flush()

    result = await repo.resolver_gtin(gtin.gtin)
    assert "error" not in result
    assert result["producto"].id == producto.id
    assert len(result["prospectos"]) == 1
    assert result["prospectos"][0].estado_vigencia == "vigente"


# ─── TC5: AuditRepository.registrar() y get_filtrado() ───────────────────────


async def test_audit_registrar_y_filtrar(db_session: AsyncSession):
    repo = AuditRepository(db_session)

    usuario1 = _make_usuario()
    usuario2 = _make_usuario()
    db_session.add_all([usuario1, usuario2])
    await db_session.flush()

    registro_id_1 = uuid.uuid4()
    registro_id_2 = uuid.uuid4()

    log1 = await repo.registrar(
        tabla_afectada="productos",
        registro_id=registro_id_1,
        accion="INSERT",
        usuario_id=usuario1.id,
    )
    log2 = await repo.registrar(
        tabla_afectada="prospectos",
        registro_id=registro_id_2,
        accion="UPDATE",
        usuario_id=usuario2.id,
        campo_modificado="estado_vigencia",
        valor_anterior="en_revision",
        valor_nuevo="vigente",
    )

    logs_productos, total = await repo.get_filtrado(tabla="productos")
    assert total >= 1
    assert any(l.tabla_afectada == "productos" for l in logs_productos)

    logs_prospectos, total2 = await repo.get_filtrado(tabla="prospectos")
    assert total2 >= 1


async def test_audit_log_trigger_inmutable(db_session: AsyncSession):
    repo = AuditRepository(db_session)

    usuario = _make_usuario()
    db_session.add(usuario)
    await db_session.flush()

    log = await repo.registrar(
        tabla_afectada="usuarios",
        registro_id=uuid.uuid4(),
        accion="INSERT",
        usuario_id=usuario.id,
    )

    # El trigger de DB bloquea UPDATE — debe lanzar excepción
    with pytest.raises(Exception, match="audit_log es inmutable"):
        await db_session.execute(
            text("UPDATE audit_log SET tabla_afectada = 'test' WHERE id = :id"),
            {"id": str(log.id)},
        )


# ─── TC6: UsuariosRepository — lockout ───────────────────────────────────────


async def test_lockout_y_reset(db_session: AsyncSession):
    repo = UsuariosRepository(db_session)

    usuario = _make_usuario()
    db_session.add(usuario)
    await db_session.flush()

    # 5 intentos fallidos → lockout
    for _ in range(5):
        await repo.registrar_intento_fallido(usuario)

    assert usuario.intentos_fallidos == 5
    assert usuario.bloqueado_hasta is not None
    assert await repo.esta_bloqueado(usuario) is True

    # Reset exitoso
    await repo.registrar_acceso_exitoso(usuario)
    assert usuario.intentos_fallidos == 0
    assert usuario.bloqueado_hasta is None
    assert await repo.esta_bloqueado(usuario) is False
