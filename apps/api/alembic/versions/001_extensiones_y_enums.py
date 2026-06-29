"""001 — Extensiones PostgreSQL y ENUMs

Revision ID: 001_extensiones_enums
Revises:
Create Date: 2026-06-29
"""

from alembic import op

revision = "001_extensiones_enums"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    op.execute("CREATE TYPE canal_enum AS ENUM ('farmacia', 'licitacion');")
    op.execute("CREATE TYPE estado_producto_enum AS ENUM ('activo', 'inactivo');")
    op.execute("CREATE TYPE estado_vigencia_enum AS ENUM ('vigente', 'reemplazado', 'en_revision');")
    op.execute(
        "CREATE TYPE tipo_audiencia_enum AS ENUM ('publico_general', 'profesional_salud', 'unico');"
    )
    op.execute("CREATE TYPE estado_gtin_enum AS ENUM ('activo', 'en_desarrollo', 'inactivo');")
    op.execute("CREATE TYPE rol_usuario_enum AS ENUM ('admin', 'editor', 'lector');")
    op.execute("CREATE TYPE accion_audit_enum AS ENUM ('INSERT', 'UPDATE', 'DELETE');")
    op.execute("CREATE TYPE tipo_envase_enum AS ENUM ('blister', 'frasco', 'otro');")


def downgrade() -> None:
    op.execute("DROP TYPE IF EXISTS tipo_envase_enum;")
    op.execute("DROP TYPE IF EXISTS accion_audit_enum;")
    op.execute("DROP TYPE IF EXISTS rol_usuario_enum;")
    op.execute("DROP TYPE IF EXISTS estado_gtin_enum;")
    op.execute("DROP TYPE IF EXISTS tipo_audiencia_enum;")
    op.execute("DROP TYPE IF EXISTS estado_vigencia_enum;")
    op.execute("DROP TYPE IF EXISTS estado_producto_enum;")
    op.execute("DROP TYPE IF EXISTS canal_enum;")

    op.execute("DROP EXTENSION IF EXISTS unaccent;")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto;")
