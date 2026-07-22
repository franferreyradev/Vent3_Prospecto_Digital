"""005 — Tabla invitaciones_usuario

Revision ID: 005_invitaciones_usuario
Revises: 004_seed_admin
Create Date: 2026-07-22
"""

from alembic import op

revision = "005_invitaciones_usuario"
down_revision = "004_seed_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE invitaciones_usuario (
            id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            email               VARCHAR(150)    NOT NULL,
            nombre              VARCHAR(100)    NOT NULL,
            rol                 rol_usuario_enum NOT NULL,
            token_hash          VARCHAR(64)     NOT NULL,
            creado_por          UUID            NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            creado_en           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            expira_en           TIMESTAMPTZ     NOT NULL,
            usado_en            TIMESTAMPTZ     NULL,
            usuario_creado_id   UUID            NULL REFERENCES usuarios(id) ON DELETE SET NULL,
            CONSTRAINT chk_invitacion_rol CHECK (rol IN ('admin', 'editor'))
        );
    """)
    op.execute(
        "CREATE UNIQUE INDEX idx_invitacion_token_hash ON invitaciones_usuario(token_hash);"
    )
    op.execute(
        "CREATE INDEX idx_invitacion_email ON invitaciones_usuario(email);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS invitaciones_usuario;")
