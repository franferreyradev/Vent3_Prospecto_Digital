from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prospecto import Prospecto
from src.repositories.productos import ProductosRepository
from src.repositories.prospectos import ProspectosRepository
from src.schemas.prospecto import ProspectoCreateRequest
from src.services.auditoria import AuditoriaService
from src.services.storage import StorageService


class ProspectosService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProspectosRepository(session)
        self.productos_repo = ProductosRepository(session)
        self.auditoria = AuditoriaService(session)
        self.storage = StorageService()

    async def subir(
        self,
        datos: ProspectoCreateRequest,
        archivo: UploadFile,
        usuario_id: UUID,
        ip_origen: str | None,
    ) -> Prospecto:
        producto = await self.productos_repo.get_by_id(datos.producto_id)
        if producto is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        contenido = await archivo.read()

        try:
            resultado = await self.storage.subir_pdf(
                contenido, archivo.filename or "prospecto.pdf", str(datos.producto_id)
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        prospecto = Prospecto(
            numero_expediente=datos.numero_expediente,
            version=datos.version,
            tipo_audiencia=datos.tipo_audiencia,
            url_archivo=resultado["url_publica"],
            nombre_archivo=archivo.filename or "prospecto.pdf",
            subido_por=usuario_id,
        )

        try:
            await self.repo.create(prospecto)
        except IntegrityError as e:
            await self.storage.eliminar_archivo(resultado["key"])
            raise HTTPException(
                status_code=409,
                detail="Ya existe un prospecto con ese número de expediente, versión y audiencia",
            ) from e

        await self.auditoria.registrar_cambio(
            tabla="prospectos",
            registro_id=prospecto.id,
            accion="INSERT",
            usuario_id=usuario_id,
            ip_origen=ip_origen,
        )

        return prospecto

    async def activar(
        self,
        prospecto_id: UUID,
        producto_id: UUID,
        usuario_id: UUID,
        ip_origen: str | None,
    ) -> dict:
        prospecto = await self.repo.get_by_id(prospecto_id)
        if prospecto is None:
            raise HTTPException(status_code=404, detail="Prospecto no encontrado")

        if prospecto.estado_vigencia != "en_revision":
            raise HTTPException(
                status_code=409, detail="El prospecto no está en estado en_revision"
            )

        resultado = await self.repo.activar_prospecto(
            producto_id, prospecto.id, prospecto.tipo_audiencia
        )

        await self.auditoria.registrar_activacion_prospecto(
            producto_id=producto_id,
            prospecto_id=prospecto.id,
            usuario_id=usuario_id,
            ip_origen=ip_origen,
        )

        return resultado
