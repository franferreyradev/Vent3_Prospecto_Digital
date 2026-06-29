"""Tests unitarios para schemas Pydantic v2. No requieren DB."""
import uuid

import pytest
from pydantic import ValidationError

from src.schemas.base import PaginatedResponse
from src.schemas.producto import ProductoCambiarEstadoRequest, ProductoListResponse
from src.schemas.prospecto import ProspectoCreateRequest
from src.schemas.resolver import ProspectoPublico, ResolverResponse
from src.schemas.usuario import LoginRequest, UsuarioResponse


def _prospecto(tipo: str) -> ProspectoPublico:
    return ProspectoPublico(tipo_audiencia=tipo, url_archivo="https://r2.example.com/f.pdf")


# TC1: un solo prospecto → tipo_landing 'unico'
def test_resolver_tipo_landing_unico():
    r = ResolverResponse(prospectos=[_prospecto("unico")])
    assert r.tipo_landing == "unico"


# TC2: dos prospectos → tipo_landing 'selector'
def test_resolver_tipo_landing_selector():
    r = ResolverResponse(
        prospectos=[_prospecto("publico_general"), _prospecto("profesional_salud")]
    )
    assert r.tipo_landing == "selector"


# TC3: con error → tipo_landing 'error'
def test_resolver_tipo_landing_error():
    r = ResolverResponse(error="no_encontrado")
    assert r.tipo_landing == "error"


# TC4: dos prospectos → tiene_dos_prospectos True
def test_resolver_tiene_dos_prospectos():
    r = ResolverResponse(
        prospectos=[_prospecto("publico_general"), _prospecto("profesional_salud")]
    )
    assert r.tiene_dos_prospectos is True


# TC5: ProspectoCreateRequest falla si version < 1
def test_prospecto_create_version_invalida():
    with pytest.raises(ValidationError):
        ProspectoCreateRequest(
            numero_expediente="IB-22/2",
            version=0,
            tipo_audiencia="unico",
            producto_id=uuid.uuid4(),
        )


# TC6: ProspectoCreateRequest falla si tipo_audiencia inválido
def test_prospecto_create_tipo_audiencia_invalido():
    with pytest.raises(ValidationError):
        ProspectoCreateRequest(
            numero_expediente="IB-22/2",
            version=1,
            tipo_audiencia="invalido",
            producto_id=uuid.uuid4(),
        )


# TC7: ProductoCambiarEstadoRequest falla con estado fuera del Literal
def test_producto_cambiar_estado_invalido():
    with pytest.raises(ValidationError):
        ProductoCambiarEstadoRequest(estado="pendiente")


# TC8: LoginRequest falla si password tiene menos de 8 caracteres
def test_login_request_password_corta():
    with pytest.raises(ValidationError):
        LoginRequest(email="admin@vent3.com", password="abc123")


# TC9: UsuarioResponse no serializa password_hash
def test_usuario_response_no_expone_password_hash():
    data = {
        "id": uuid.uuid4(),
        "email": "admin@vent3.com",
        "nombre": "Admin",
        "rol": "admin",
        "activo": True,
        "ultimo_acceso": None,
        "created_at": "2026-06-29T00:00:00Z",
        "password_hash": "should_not_appear",
    }
    r = UsuarioResponse.model_validate(data)
    serialized = r.model_dump()
    assert "password_hash" not in serialized


# TC10: PaginatedResponse[ProductoListResponse] se instancia correctamente
def test_paginated_response_productos():
    item = ProductoListResponse(
        id=uuid.uuid4(),
        codigo_interno="MED001",
        nombre_comercial="Ibuprofeno 400mg",
        forma_farmaceutica="Comprimidos",
        presentacion_cantidad="20 comp",
        canal="farmacia",
        estado="activo",
        tiene_prospecto=True,
    )
    page = PaginatedResponse[ProductoListResponse](
        data=[item], total=1, page=1, limit=20
    )
    assert page.total == 1
    assert page.data[0].nombre_comercial == "Ibuprofeno 400mg"
