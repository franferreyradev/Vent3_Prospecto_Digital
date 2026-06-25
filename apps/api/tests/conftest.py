import os

# Setear antes de importar cualquier módulo de la aplicación,
# porque Settings() se instancia al nivel de módulo en config.py.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://vent3:vent3dev@localhost:5432/vent3_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-64-chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("ADMIN_INITIAL_PASSWORD", "test-password")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal-token")
os.environ.setdefault("R2_ACCOUNT_ID", "test-account-id")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-access-key")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-secret-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-bucket")
os.environ.setdefault("R2_PUBLIC_URL", "https://test.r2.dev")
