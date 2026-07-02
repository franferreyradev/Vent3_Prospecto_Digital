import asyncio
import re
import uuid

from src.core.config import settings
from src.core.r2_client import r2

PRESIGNED_URL_EXPIRATION = 300  # 5 minutos
TAMANO_MAXIMO_BYTES = 20 * 1024 * 1024  # 20 MB
MAGIC_BYTES_PDF = b"%PDF"


def sanitizar_nombre_archivo(nombre: str) -> str:
    nombre = nombre.lower().strip()
    nombre = re.sub(r"[^a-z0-9._-]+", "_", nombre)
    nombre = re.sub(r"_+", "_", nombre)
    return nombre.strip("_")


def generar_key(producto_id: str, nombre_archivo: str) -> str:
    nombre_sanitizado = sanitizar_nombre_archivo(nombre_archivo)
    return f"prospectos/{producto_id}/{uuid.uuid4()}_{nombre_sanitizado}"


class StorageService:
    async def subir_pdf(self, contenido: bytes, nombre_archivo: str, producto_id: str) -> dict:
        if not contenido.startswith(MAGIC_BYTES_PDF):
            raise ValueError("Archivo no es un PDF válido")

        if len(contenido) > TAMANO_MAXIMO_BYTES:
            raise ValueError("Archivo supera el tamaño máximo de 20 MB")

        key = generar_key(producto_id, nombre_archivo)
        nombre_sanitizado = sanitizar_nombre_archivo(nombre_archivo)

        await asyncio.to_thread(
            r2.put_object,
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=contenido,
            ContentType="application/pdf",
            ContentDisposition=f'inline; filename="{nombre_sanitizado}"',
        )

        url_publica = f"{settings.R2_PUBLIC_URL}/{key}"

        return {
            "key": key,
            "url_publica": url_publica,
            "nombre_archivo": nombre_archivo,
        }

    async def generar_url_firmada(self, key: str) -> str:
        return await asyncio.to_thread(
            r2.generate_presigned_url,
            "get_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION,
        )

    async def eliminar_archivo(self, key: str) -> None:
        await asyncio.to_thread(
            r2.delete_object,
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
        )
