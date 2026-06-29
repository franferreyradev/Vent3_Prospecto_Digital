import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.models.base import Base
from src.models import (  # noqa: F401 — side effect: registra todos los modelos en Base.metadata
    Usuario,
    Producto,
    PrincipioActivo,
    ProductoPrincipio,
    Prospecto,
    ProductoProspecto,
    GtinRegistro,
    AuditLog,
    ProductoMaterialesPackaging,
)

target_metadata = Base.metadata


def get_url() -> str:
    from src.core.config import settings
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    # Los índices son creados por SQL raw en las migraciones (no en los modelos).
    # Ignorar índices que están en la DB pero no en los modelos para evitar
    # falsos positivos en alembic check/autogenerate.
    if type_ == "index" and reflected and compare_to is None:
        return False
    return True


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
