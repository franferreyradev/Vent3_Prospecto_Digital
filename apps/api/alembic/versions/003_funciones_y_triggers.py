"""003 — Funciones PL/pgSQL y triggers

Revision ID: 003_funciones_triggers
Revises: 002_tablas_core
Create Date: 2026-06-29
"""

from alembic import op

revision = "003_funciones_triggers"
down_revision = "002_tablas_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Función 1: actualizar updated_at automáticamente
    op.execute("""
        CREATE OR REPLACE FUNCTION actualizar_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_updated_at_productos
        BEFORE UPDATE ON productos
        FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();
    """)

    op.execute("""
        CREATE TRIGGER trg_updated_at_producto_materiales_packaging
        BEFORE UPDATE ON producto_materiales_packaging
        FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();
    """)

    # Función 2: normalizar nombre de principio activo (lower + unaccent)
    op.execute("""
        CREATE OR REPLACE FUNCTION normalizar_principio_activo()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.nombre_normalizado = lower(unaccent(NEW.nombre));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_normalizar_principio_activo
        BEFORE INSERT OR UPDATE ON principios_activos
        FOR EACH ROW EXECUTE FUNCTION normalizar_principio_activo();
    """)

    # Función 3: bloquear UPDATE y DELETE en audit_log (inmutabilidad total)
    op.execute("""
        CREATE OR REPLACE FUNCTION raise_audit_inmutable()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log es inmutable: no se permiten UPDATE ni DELETE';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_inmutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION raise_audit_inmutable();
    """)

    # Permisos de DB: si existe el rol vent3_app, revocar UPDATE/DELETE sobre audit_log.
    # En Railway se usa el rol por defecto (no existe vent3_app), así que el bloque
    # es condicional y no falla si el rol no existe.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vent3_app') THEN
                REVOKE UPDATE, DELETE ON audit_log FROM vent3_app;
            END IF;
        END;
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_inmutable ON audit_log;")
    op.execute("DROP TRIGGER IF EXISTS trg_normalizar_principio_activo ON principios_activos;")
    op.execute("DROP TRIGGER IF EXISTS trg_updated_at_producto_materiales_packaging ON producto_materiales_packaging;")
    op.execute("DROP TRIGGER IF EXISTS trg_updated_at_productos ON productos;")

    op.execute("DROP FUNCTION IF EXISTS raise_audit_inmutable();")
    op.execute("DROP FUNCTION IF EXISTS normalizar_principio_activo();")
    op.execute("DROP FUNCTION IF EXISTS actualizar_updated_at();")
