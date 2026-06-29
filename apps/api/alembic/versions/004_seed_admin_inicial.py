"""004 — Seed del usuario admin inicial

Revision ID: 004_seed_admin
Revises: 003_funciones_triggers
Create Date: 2026-06-29
"""

import os

from alembic import op
from sqlalchemy import text

revision = "004_seed_admin"
down_revision = "003_funciones_triggers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")

    if not admin_email:
        raise ValueError(
            "Variable ADMIN_EMAIL requerida para seed inicial. "
            "Definila en el entorno antes de correr 'alembic upgrade head'."
        )
    if not admin_password:
        raise ValueError(
            "Variable ADMIN_INITIAL_PASSWORD requerida para seed inicial. "
            "Definila en el entorno antes de correr 'alembic upgrade head'."
        )

    import bcrypt as _bcrypt

    password_hash = _bcrypt.hashpw(
        admin_password.encode("utf-8"),
        _bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    bind = op.get_bind()
    bind.execute(
        text("""
            INSERT INTO usuarios (
                id, email, nombre, password_hash, rol, activo, intentos_fallidos, created_at
            ) VALUES (
                gen_random_uuid(), :email, 'Administrador', :password_hash,
                'admin', TRUE, 0, NOW()
            )
            ON CONFLICT (email) DO NOTHING
        """),
        {"email": admin_email, "password_hash": password_hash},
    )


def downgrade() -> None:
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        bind = op.get_bind()
        bind.execute(
            text("DELETE FROM usuarios WHERE email = :email"),
            {"email": admin_email},
        )
