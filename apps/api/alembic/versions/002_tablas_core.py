"""002 — Tablas core con constraints, FKs e índices

Revision ID: 002_tablas_core
Revises: 001_extensiones_enums
Create Date: 2026-06-29
"""

from alembic import op

revision = "002_tablas_core"
down_revision = "001_extensiones_enums"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. usuarios — sin dependencias
    op.execute("""
        CREATE TABLE usuarios (
            id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            email           VARCHAR(150)    NOT NULL UNIQUE,
            nombre          VARCHAR(100)    NOT NULL,
            password_hash   VARCHAR(60)     NOT NULL,
            rol             rol_usuario_enum NOT NULL DEFAULT 'lector',
            activo          BOOLEAN         NOT NULL DEFAULT TRUE,
            ultimo_acceso   TIMESTAMPTZ     NULL,
            intentos_fallidos SMALLINT      NOT NULL DEFAULT 0,
            bloqueado_hasta TIMESTAMPTZ     NULL,
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE UNIQUE INDEX idx_usuario_email ON usuarios(email);"
    )

    # 2. productos — sin dependencias
    op.execute("""
        CREATE TABLE productos (
            id                      UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
            codigo_interno          VARCHAR(20)             NULL UNIQUE,
            nombre_comercial        VARCHAR(200)            NOT NULL,
            forma_farmaceutica      VARCHAR(100)            NOT NULL,
            presentacion_cantidad   VARCHAR(50)             NOT NULL,
            canal                   canal_enum              NOT NULL DEFAULT 'farmacia',
            estado                  estado_producto_enum    NOT NULL DEFAULT 'activo',
            tiene_prospecto         BOOLEAN                 NOT NULL DEFAULT FALSE,
            created_at              TIMESTAMPTZ             NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ             NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE INDEX idx_producto_estado ON productos(estado) WHERE estado = 'activo';"
    )
    op.execute("CREATE INDEX idx_producto_canal ON productos(canal);")
    op.execute("CREATE INDEX idx_producto_codigo_interno ON productos(codigo_interno);")

    # 3. principios_activos — sin dependencias
    op.execute("""
        CREATE TABLE principios_activos (
            id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            nombre              VARCHAR(150) NOT NULL UNIQUE,
            nombre_normalizado  VARCHAR(150) NOT NULL UNIQUE,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE INDEX idx_principio_normalizado ON principios_activos(nombre_normalizado);"
    )

    # 4. producto_principios — depende de productos y principios_activos
    op.execute("""
        CREATE TABLE producto_principios (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            producto_id     UUID        NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
            principio_id    UUID        NOT NULL REFERENCES principios_activos(id) ON DELETE RESTRICT,
            potencia        VARCHAR(30) NOT NULL,
            unidad          VARCHAR(20) NULL,
            orden           SMALLINT    NOT NULL CHECK (orden > 0),
            UNIQUE (producto_id, principio_id)
        );
    """)
    op.execute("CREATE INDEX idx_pp_producto ON producto_principios(producto_id);")
    op.execute("CREATE INDEX idx_pp_principio ON producto_principios(principio_id);")

    # 5. prospectos — depende de usuarios
    op.execute("""
        CREATE TABLE prospectos (
            id                  UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
            numero_expediente   VARCHAR(30)             NOT NULL,
            version             SMALLINT                NOT NULL CHECK (version > 0),
            tipo_audiencia      tipo_audiencia_enum     NOT NULL DEFAULT 'unico',
            url_archivo         TEXT                    NOT NULL,
            nombre_archivo      VARCHAR(200)            NOT NULL,
            estado_vigencia     estado_vigencia_enum    NOT NULL DEFAULT 'en_revision',
            subido_por          UUID                    NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            created_at          TIMESTAMPTZ             NOT NULL DEFAULT NOW(),
            UNIQUE (numero_expediente, version, tipo_audiencia)
        );
    """)
    op.execute(
        "CREATE INDEX idx_prospecto_vigente ON prospectos(estado_vigencia) "
        "WHERE estado_vigencia = 'vigente';"
    )
    op.execute("CREATE INDEX idx_prospecto_numero ON prospectos(numero_expediente);")

    # 6. producto_prospectos — depende de productos y prospectos
    op.execute("""
        CREATE TABLE producto_prospectos (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            producto_id     UUID        NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
            prospecto_id    UUID        NOT NULL REFERENCES prospectos(id) ON DELETE RESTRICT,
            variante_gs1    VARCHAR(30) NULL,
            activo          BOOLEAN     NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_pp_unico_vigente
        ON producto_prospectos(producto_id, prospecto_id)
        WHERE activo = TRUE;
    """)
    op.execute(
        "CREATE INDEX idx_prodprosp_producto ON producto_prospectos(producto_id);"
    )
    op.execute(
        "CREATE INDEX idx_prodprosp_activo ON producto_prospectos(producto_id) WHERE activo = TRUE;"
    )

    # 7. gtin_registro — depende de productos
    op.execute("""
        CREATE TABLE gtin_registro (
            id              UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
            producto_id     UUID                NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
            gtin            CHAR(14)            NOT NULL CHECK (gtin ~ '^\\d{14}$'),
            estado_gtin     estado_gtin_enum    NOT NULL DEFAULT 'en_desarrollo',
            es_vigente      BOOLEAN             NOT NULL DEFAULT FALSE,
            url_digital_link TEXT               NULL,
            qr_generado     BOOLEAN             NOT NULL DEFAULT FALSE,
            validado_gs1    BOOLEAN             NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
            UNIQUE (gtin)
        );
    """)
    op.execute(
        "CREATE UNIQUE INDEX idx_gtin_vigente_unico ON gtin_registro(producto_id) "
        "WHERE es_vigente = TRUE;"
    )
    op.execute("CREATE UNIQUE INDEX idx_gtin_lookup ON gtin_registro(gtin);")
    op.execute("CREATE INDEX idx_gtin_producto ON gtin_registro(producto_id);")

    # 8. audit_log — depende de usuarios
    op.execute("""
        CREATE TABLE audit_log (
            id                  UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
            tabla_afectada      VARCHAR(50)         NOT NULL,
            registro_id         UUID                NOT NULL,
            accion              accion_audit_enum   NOT NULL,
            campo_modificado    VARCHAR(80)         NULL,
            valor_anterior      TEXT                NULL,
            valor_nuevo         TEXT                NULL,
            usuario_id          UUID                NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            ip_origen           INET                NULL,
            created_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE INDEX idx_audit_tabla_registro ON audit_log(tabla_afectada, registro_id);"
    )
    op.execute("CREATE INDEX idx_audit_usuario ON audit_log(usuario_id);")
    op.execute("CREATE INDEX idx_audit_created ON audit_log(created_at DESC);")

    # 9. producto_materiales_packaging — depende de productos
    op.execute("""
        CREATE TABLE producto_materiales_packaging (
            id                  UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
            producto_id         UUID                NOT NULL UNIQUE REFERENCES productos(id) ON DELETE CASCADE,
            tipo_envase         tipo_envase_enum    NOT NULL,
            codigo_estuche      VARCHAR(30)         NULL,
            codigo_aluminio     VARCHAR(30)         NULL,
            codigo_pvc          VARCHAR(30)         NULL,
            codigo_frasco       VARCHAR(30)         NULL,
            codigo_etiqueta     VARCHAR(30)         NULL,
            codigo_vaso_inserto VARCHAR(30)         NULL,
            codigo_tapa         VARCHAR(30)         NULL,
            notas               TEXT                NULL,
            created_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW()
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS producto_materiales_packaging;")
    op.execute("DROP TABLE IF EXISTS audit_log;")
    op.execute("DROP TABLE IF EXISTS gtin_registro;")
    op.execute("DROP TABLE IF EXISTS producto_prospectos;")
    op.execute("DROP TABLE IF EXISTS prospectos;")
    op.execute("DROP TABLE IF EXISTS producto_principios;")
    op.execute("DROP TABLE IF EXISTS principios_activos;")
    op.execute("DROP TABLE IF EXISTS productos;")
    op.execute("DROP TABLE IF EXISTS usuarios;")
