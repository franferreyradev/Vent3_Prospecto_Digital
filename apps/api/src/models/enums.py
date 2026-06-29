"""ENUMs de PostgreSQL — todos con create_type=False porque ya existen en la DB."""
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

canal_enum = PgEnum("farmacia", "licitacion", name="canal_enum", create_type=False)
estado_producto_enum = PgEnum("activo", "inactivo", name="estado_producto_enum", create_type=False)
estado_vigencia_enum = PgEnum(
    "vigente", "reemplazado", "en_revision", name="estado_vigencia_enum", create_type=False
)
tipo_audiencia_enum = PgEnum(
    "publico_general", "profesional_salud", "unico", name="tipo_audiencia_enum", create_type=False
)
estado_gtin_enum = PgEnum(
    "activo", "en_desarrollo", "inactivo", name="estado_gtin_enum", create_type=False
)
rol_usuario_enum = PgEnum("admin", "editor", "lector", name="rol_usuario_enum", create_type=False)
accion_audit_enum = PgEnum("INSERT", "UPDATE", "DELETE", name="accion_audit_enum", create_type=False)
tipo_envase_enum = PgEnum("blister", "frasco", "otro", name="tipo_envase_enum", create_type=False)
