from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import TypeAdapter
from sqlalchemy import text

from src.core.config import settings
from src.routers.audit import router as audit_router
from src.routers.auth import router as auth_router
from src.routers.gtins import router as gtins_router
from src.routers.internal import router as internal_router
from src.routers.invitaciones import router as invitaciones_router
from src.routers.productos import router as productos_router
from src.routers.prospectos import router as prospectos_router
from src.routers.usuarios import router as usuarios_router
from src.schemas import (
    AuditLogResponse,
    GtinRegistroResponse,
    PaginatedResponse,
    ProductoDetalleResponse,
    ProductoListResponse,
    ProspectoResponse,
    ResolverResponse,
    UsuarioResponse,
)
from src.schemas.base import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from src.core.db import engine

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield


app = FastAPI(
    title="Vent3 API",
    description="Sistema de Prospecto Digital ANMAT — Laboratorio Vent3",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas a incluir en el OpenAPI aunque no estén wired a endpoints todavía.
# Se actualizan automáticamente a medida que se agregan routers en T6+.
_SCHEMA_MODELS = [
    UsuarioResponse,
    ProductoListResponse,
    ProductoDetalleResponse,
    ProspectoResponse,
    ResolverResponse,
    AuditLogResponse,
    GtinRegistroResponse,
    TypeAdapter(PaginatedResponse[ProductoListResponse]),
]


def _custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema  # type: ignore[return-value]

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Inyectar schemas no wired a endpoints para que aparezcan en el OpenAPI.
    components = schema.setdefault("components", {})
    schemas_section = components.setdefault("schemas", {})
    for model in _SCHEMA_MODELS:
        if isinstance(model, TypeAdapter):
            json_schema = model.json_schema(ref_template="#/components/schemas/{model}")
        else:
            json_schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        # Extraer $defs anidados al nivel de components/schemas antes de insertar.
        nested_defs = json_schema.pop("$defs", {})
        for def_name, def_schema in nested_defs.items():
            if def_name not in schemas_section:
                # Limpiar $defs recursivos si los hubiera
                def_schema.pop("$defs", None)
                schemas_section[def_name] = def_schema
        title = json_schema.get("title", "")
        if title and title not in schemas_section:
            schemas_section[title] = json_schema

    app.openapi_schema = schema
    return schema  # type: ignore[return-value]


app.openapi = _custom_openapi  # type: ignore[method-assign]

app.include_router(auth_router)
app.include_router(productos_router)
app.include_router(prospectos_router)
app.include_router(gtins_router)
app.include_router(internal_router)
app.include_router(audit_router)
app.include_router(invitaciones_router)
app.include_router(usuarios_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")
