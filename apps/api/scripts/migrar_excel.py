"""Migración one-shot desde BD_productos_v2.xlsx hacia la base de datos.

Uso: uv run python scripts/migrar_excel.py [ruta_al_xlsx]

Idempotente: una segunda ejecución sobre la misma DB no duplica productos
(se saltea por `codigo_interno`) ni principios activos (se saltea por
`nombre_normalizado`).
"""
from __future__ import annotations

import asyncio
import sys
import unicodedata
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    # Permite `uv run python scripts/migrar_excel.py` sin depender de -m,
    # agregando apps/api/ (el padre de este archivo) al sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import AsyncSessionLocal
from src.models import GtinRegistro, PrincipioActivo, Producto, ProductoMaterialesPackaging, ProductoPrincipio

EXCEL_PATH_DEFAULT = Path(__file__).parent / "data" / "BD_productos_v2.xlsx"
GTIN_PREFIX = "02"  # GS1 Restricted Circulation Number — nunca asignado como GTIN real


def normalizar(nombre: str) -> str:
    """Replica `lower(unaccent(nombre))` del trigger de DB (sin trim, eso se hace antes)."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    return sin_acentos.lower()


def limpiar_texto(valor) -> str | None:
    """Trimea strings y convierte el literal 'N/A' del Excel en NULL."""
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if valor == "" or valor.upper() == "N/A":
            return None
        return valor
    return str(valor)


def es_licitacion(presentacion) -> bool:
    return isinstance(presentacion, str) and "licita" in presentacion.lower()


def es_en_proceso(presentacion) -> bool:
    return isinstance(presentacion, str) and "proceso" in presentacion.lower()


def digito_verificador_gtin14(base13: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(base13)):
        peso = 3 if i % 2 == 0 else 1
        total += int(ch) * peso
    return str((10 - total % 10) % 10)


def generar_gtin(contador: int) -> str:
    base13 = f"{GTIN_PREFIX}{contador:011d}"
    return base13 + digito_verificador_gtin14(base13)


def leer_bloques(ws) -> list[dict]:
    """Agrupa las filas de la hoja en bloques de producto, resolviendo huérfanas."""
    bloques: list[dict] = []
    bloque_actual: dict | None = None

    for row in ws.iter_rows(min_row=2, values_only=True):
        codigo_interno, producto_nombre, droga, potencia = row[1], row[2], row[3], row[4]
        forma_farmaceutica, presentacion, estado_raw = row[5], row[6], row[7]
        estuche, aluminio, pvc, frasco = row[9], row[10], row[11], row[12]
        etiqueta, vaso_inserto, tapa = row[13], row[14], row[15]

        if codigo_interno not in (None, ""):
            bloque_actual = {
                "codigo_interno": str(codigo_interno).strip(),
                "producto": producto_nombre,
                "forma_farmaceutica": forma_farmaceutica,
                "presentacion": presentacion,
                "estado": estado_raw,
                "principios": [(droga, potencia)] if droga not in (None, "") else [],
                "estuche": estuche,
                "aluminio": aluminio,
                "pvc": pvc,
                "frasco": frasco,
                "etiqueta": etiqueta,
                "vaso_inserto": vaso_inserto,
                "tapa": tapa,
                "frascos_secundarios": [],
            }
            bloques.append(bloque_actual)
        elif bloque_actual is not None:
            if droga not in (None, ""):
                bloque_actual["principios"].append((droga, potencia))
            elif frasco not in (None, ""):
                bloque_actual["frascos_secundarios"].append(str(frasco).strip())

    return bloques


async def obtener_o_crear_principio(session: AsyncSession, nombre_crudo: str) -> tuple[PrincipioActivo, bool]:
    nombre = str(nombre_crudo).strip()
    normalizado = normalizar(nombre)

    result = await session.execute(
        select(PrincipioActivo).where(PrincipioActivo.nombre_normalizado == normalizado)
    )
    principio = result.scalar_one_or_none()
    if principio is not None:
        return principio, False

    principio = PrincipioActivo(nombre=nombre)
    session.add(principio)
    await session.flush()
    await session.refresh(principio, attribute_names=["nombre_normalizado"])
    return principio, True


async def siguiente_contador_gtin(session: AsyncSession) -> int:
    result = await session.execute(
        select(GtinRegistro.gtin).where(GtinRegistro.gtin.like(f"{GTIN_PREFIX}%"))
    )
    maximo = 0
    for (gtin,) in result:
        maximo = max(maximo, int(gtin[2:13]))
    return maximo + 1


async def migrar(session: AsyncSession, bloques: list[dict]) -> dict:
    stats = {
        "productos_creados": 0,
        "productos_saltados": 0,
        "principios_creados": 0,
        "principios_reusados": 0,
        "en_proceso_ignorados": 0,
    }
    contador_gtin = await siguiente_contador_gtin(session)

    for bloque in bloques:
        presentacion = bloque["presentacion"]

        if es_en_proceso(presentacion):
            stats["en_proceso_ignorados"] += 1
            continue

        existente = await session.execute(
            select(Producto).where(Producto.codigo_interno == bloque["codigo_interno"])
        )
        if existente.scalar_one_or_none() is not None:
            stats["productos_saltados"] += 1
            continue

        if es_licitacion(presentacion):
            canal = "licitacion"
            presentacion_cantidad = "licitacion"
        else:
            canal = "farmacia"
            presentacion_cantidad = str(presentacion)

        if bloque["estado"] == "A":
            estado = "activo"
        elif bloque["estado"] == "I":
            estado = "inactivo"
        else:
            raise ValueError(
                f"ESTADO desconocido '{bloque['estado']}' en producto {bloque['codigo_interno']}"
            )

        producto = Producto(
            codigo_interno=bloque["codigo_interno"],
            nombre_comercial=bloque["producto"],
            forma_farmaceutica=bloque["forma_farmaceutica"],
            presentacion_cantidad=presentacion_cantidad,
            canal=canal,
            estado=estado,
        )
        session.add(producto)
        await session.flush()

        for orden, (droga, potencia) in enumerate(bloque["principios"], start=1):
            principio, creado = await obtener_o_crear_principio(session, droga)
            stats["principios_creados" if creado else "principios_reusados"] += 1
            session.add(
                ProductoPrincipio(
                    producto_id=producto.id,
                    principio_id=principio.id,
                    potencia=str(potencia).strip(),
                    unidad=None,
                    orden=orden,
                )
            )

        aluminio = limpiar_texto(bloque["aluminio"])
        pvc = limpiar_texto(bloque["pvc"])
        frasco = limpiar_texto(bloque["frasco"])
        if aluminio is not None or pvc is not None:
            tipo_envase = "blister"
        elif frasco is not None:
            tipo_envase = "frasco"
        else:
            tipo_envase = "otro"

        notas = None
        if bloque["frascos_secundarios"]:
            notas = "; ".join(f"Frasco alternativo: {c}" for c in bloque["frascos_secundarios"])

        session.add(
            ProductoMaterialesPackaging(
                producto_id=producto.id,
                tipo_envase=tipo_envase,
                codigo_estuche=limpiar_texto(bloque["estuche"]),
                codigo_aluminio=aluminio,
                codigo_pvc=pvc,
                codigo_frasco=frasco,
                codigo_etiqueta=limpiar_texto(bloque["etiqueta"]),
                codigo_vaso_inserto=limpiar_texto(bloque["vaso_inserto"]),
                codigo_tapa=limpiar_texto(bloque["tapa"]),
                notas=notas,
            )
        )

        session.add(
            GtinRegistro(
                producto_id=producto.id,
                gtin=generar_gtin(contador_gtin),
                estado_gtin="en_desarrollo",
                es_vigente=False,
                qr_generado=False,
                validado_gs1=False,
            )
        )
        contador_gtin += 1

        stats["productos_creados"] += 1

    await session.commit()
    return stats


async def main(excel_path: Path) -> None:
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb["Hoja1"]
    bloques = leer_bloques(ws)

    async with AsyncSessionLocal() as session:
        stats = await migrar(session, bloques)

    print("Migración completada:")
    print(f"  Productos creados:       {stats['productos_creados']}")
    print(f"  Productos salteados:     {stats['productos_saltados']} (ya existían)")
    print(f"  Principios creados:      {stats['principios_creados']}")
    print(f"  Principios reusados:     {stats['principios_reusados']}")
    print(f"  Filas 'en proceso':      {stats['en_proceso_ignorados']} (ignoradas)")


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else EXCEL_PATH_DEFAULT
    asyncio.run(main(ruta))
