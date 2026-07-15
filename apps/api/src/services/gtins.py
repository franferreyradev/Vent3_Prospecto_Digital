from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gtin_registro import GtinRegistro
from src.models.usuario import Usuario
from src.repositories.gtins import GtinsRepository
from src.schemas.gtin import GtinUpdateRequest
from src.services.auditoria import AuditoriaService

# Una vez generado el QR, "qr_generado" y la URL de Digital Link pueden estar
# ya impresos en packaging físico en circulación (RNF-08). Revertir la marca
# o cambiar la URL rompería el código impreso. Esto queda como vía de
# corrección de error humano exclusiva del rol admin (ver
# docs/adr/002-inmutabilidad-gtin-qr.md) — un editor puede cargarlos una sola
# vez, nunca modificarlos después de guardados con qr_generado=true.
CAMPOS_SOLO_ADMIN_CON_QR_GENERADO = {"qr_generado", "url_digital_link"}


class GtinsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GtinsRepository(session)
        self.auditoria = AuditoriaService(session)

    async def actualizar(
        self,
        id: UUID,
        datos: GtinUpdateRequest,
        usuario: Usuario,
        ip_origen: str | None,
    ) -> GtinRegistro:
        gtin_registro = await self.repo.get_by_id(id)
        if gtin_registro is None:
            raise HTTPException(status_code=404, detail="GTIN no encontrado")

        campos_modificados = datos.model_dump(exclude_none=True)

        # El GTIN queda permanente una vez generado el QR: ese número puede
        # estar ya impreso en packaging físico, cambiarlo rompería el código
        # en circulación (RNF-08). Esto es incondicional para cualquier rol:
        # la única vía de corrección es desmarcar "qr_generado" primero (ver
        # chequeo siguiente, exclusivo de admin) y recién ahí editar el GTIN
        # en un segundo PATCH.
        if "gtin" in campos_modificados and gtin_registro.qr_generado:
            raise HTTPException(
                status_code=409,
                detail="No se puede modificar el GTIN de un registro con QR ya generado",
            )

        if (
            gtin_registro.qr_generado
            and usuario.rol != "admin"
            and CAMPOS_SOLO_ADMIN_CON_QR_GENERADO & campos_modificados.keys()
        ):
            raise HTTPException(
                status_code=403,
                detail="Solo un administrador puede modificar un registro con QR ya generado",
            )

        # Solo puede haber un GTIN vigente por producto (constraint parcial
        # idx_gtin_vigente_unico). Al marcar uno como vigente, el anterior
        # (si existe) se reemplaza automáticamente — mismo patrón que
        # activar_prospecto() con los prospectos. Se confirma y audita el
        # reemplazo ANTES de tocar la fila actual, para no chocar contra la
        # constraint mientras ambas filas están "vigente=true" a la vez.
        if campos_modificados.get("es_vigente") is True:
            anterior_vigente = await self.repo.get_vigente_por_producto(
                gtin_registro.producto_id, excluir_id=gtin_registro.id
            )
            if anterior_vigente is not None:
                anterior_vigente.es_vigente = False
                await self.repo.update(anterior_vigente)
                await self.auditoria.registrar_cambio(
                    tabla="gtin_registro",
                    registro_id=anterior_vigente.id,
                    accion="UPDATE",
                    usuario_id=usuario.id,
                    campo="es_vigente",
                    valor_anterior=True,
                    valor_nuevo=False,
                    ip_origen=ip_origen,
                )

        # Se capturan los valores anteriores y se aplica + confirma el UPDATE
        # ANTES de auditar: AuditoriaService.registrar_cambio() hace su propio
        # flush(), que arrastra cualquier cambio pendiente de esta sesión (no
        # solo la fila de audit_log). Si el UPDATE real violara una constraint
        # (ej. gtin duplicado), ese flush "prestado" tragaría el error dentro
        # del try/except defensivo de AuditoriaService — el 409 nunca llegaría
        # al usuario. Confirmando el cambio primero, el conflicto sale limpio
        # acá, y solo se audita lo que realmente se persistió.
        valores_anteriores = {
            campo: getattr(gtin_registro, campo) for campo in campos_modificados
        }
        for campo, valor_nuevo in campos_modificados.items():
            setattr(gtin_registro, campo, valor_nuevo)

        try:
            await self.repo.update(gtin_registro)
        except IntegrityError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Ese GTIN ya está registrado para otro producto",
            ) from e

        for campo, valor_nuevo in campos_modificados.items():
            await self.auditoria.registrar_cambio(
                tabla="gtin_registro",
                registro_id=gtin_registro.id,
                accion="UPDATE",
                usuario_id=usuario.id,
                campo=campo,
                valor_anterior=valores_anteriores[campo],
                valor_nuevo=valor_nuevo,
                ip_origen=ip_origen,
            )

        return gtin_registro
