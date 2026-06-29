import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PrincipioActivoEnProducto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    potencia: str
    unidad: str | None
    orden: int


class ProductoListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_interno: str | None
    nombre_comercial: str
    forma_farmaceutica: str
    presentacion_cantidad: str
    canal: str
    estado: str
    tiene_prospecto: bool


class ProductoDetalleResponse(ProductoListResponse):
    principios: list[PrincipioActivoEnProducto]
    created_at: datetime
    updated_at: datetime


class ProductoUpdateRequest(BaseModel):
    nombre_comercial: str | None = None
    forma_farmaceutica: str | None = None
    presentacion_cantidad: str | None = None


class ProductoCambiarEstadoRequest(BaseModel):
    estado: Literal["activo", "inactivo"]
