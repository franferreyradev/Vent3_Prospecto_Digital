import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field


class ProspectoPublico(BaseModel):
    tipo_audiencia: str
    url_archivo: str


class ProductoPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre_comercial: str
    forma_farmaceutica: str
    presentacion_cantidad: str


class ResolverResponse(BaseModel):
    producto: ProductoPublico | None = None
    prospectos: list[ProspectoPublico] = []
    error: Literal["no_encontrado", "inactivo", "sin_prospecto"] | None = None

    @computed_field
    @property
    def tiene_dos_prospectos(self) -> bool:
        return len(self.prospectos) == 2

    @computed_field
    @property
    def tipo_landing(self) -> Literal["unico", "selector", "error"]:
        if self.error:
            return "error"
        if self.tiene_dos_prospectos:
            return "selector"
        return "unico"
