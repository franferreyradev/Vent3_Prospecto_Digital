"""
TC1-TC6: Tests unitarios del servicio de storage (T10).
No requieren DB ni R2 real — r2.put_object/generate_presigned_url/delete_object mockeados.
"""

from unittest.mock import patch

import pytest

from src.core.config import settings
from src.services.storage import (
    StorageService,
    generar_key,
    sanitizar_nombre_archivo,
)

PDF_VALIDO = b"%PDF-1.4 contenido de prueba"
PRODUCTO_ID = "a1b2c3d4-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_subir_pdf_valido_retorna_key_y_url_publica():
    service = StorageService()

    with patch("src.services.storage.r2") as mock_r2:
        resultado = await service.subir_pdf(
            contenido=PDF_VALIDO,
            nombre_archivo="Prospecto Ibuprofeno.pdf",
            producto_id=PRODUCTO_ID,
        )

    assert resultado["key"].startswith(f"prospectos/{PRODUCTO_ID}/")
    assert resultado["url_publica"].startswith(settings.R2_PUBLIC_URL)
    mock_r2.put_object.assert_called_once()
    kwargs = mock_r2.put_object.call_args.kwargs
    assert kwargs["ContentType"] == "application/pdf"


@pytest.mark.asyncio
async def test_subir_pdf_contenido_no_es_pdf_lanza_value_error():
    service = StorageService()

    with pytest.raises(ValueError, match="no es un PDF válido"):
        await service.subir_pdf(
            contenido=b"esto no es un pdf",
            nombre_archivo="falso.pdf",
            producto_id=PRODUCTO_ID,
        )


@pytest.mark.asyncio
async def test_subir_pdf_supera_tamano_maximo_lanza_value_error():
    service = StorageService()
    contenido_grande = b"%PDF-1.4" + b"0" * (21 * 1024 * 1024)

    with pytest.raises(ValueError, match="tamaño máximo"):
        await service.subir_pdf(
            contenido=contenido_grande,
            nombre_archivo="grande.pdf",
            producto_id=PRODUCTO_ID,
        )


@pytest.mark.asyncio
async def test_subir_pdf_sanitiza_nombre_de_archivo():
    service = StorageService()

    with patch("src.services.storage.r2"):
        resultado = await service.subir_pdf(
            contenido=PDF_VALIDO,
            nombre_archivo="Prospecto Ibuprofeno (v2).pdf",
            producto_id=PRODUCTO_ID,
        )

    assert " " not in resultado["key"]
    assert "(" not in resultado["key"]
    assert ")" not in resultado["key"]
    assert "prospecto_ibuprofeno_v2_.pdf" in resultado["key"]


@pytest.mark.asyncio
async def test_generar_url_firmada_retorna_url_del_mock():
    service = StorageService()
    url_esperada = "https://r2.example.com/presigned?sig=abc123"

    with patch("src.services.storage.r2") as mock_r2:
        mock_r2.generate_presigned_url.return_value = url_esperada
        url = await service.generar_url_firmada("prospectos/x/y.pdf")

    assert url == url_esperada
    kwargs = mock_r2.generate_presigned_url.call_args.kwargs
    assert kwargs["ExpiresIn"] == 300


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Prospecto Ibuprofeno v2 (final).pdf", "prospecto_ibuprofeno_v2_final_.pdf"),
        ("prospecto niño ñandú.pdf", "prospecto_ni_o_and_.pdf"),
        ("  espacios   multiples  .pdf", "espacios_multiples_.pdf"),
        ("CAPS-Y-Símbolos!@#.pdf", "caps-y-s_mbolos_.pdf"),
    ],
)
def test_sanitizar_nombre_archivo_casos_edge(entrada, esperado):
    assert sanitizar_nombre_archivo(entrada) == esperado


def test_generar_key_incluye_prefijo_prospectos_y_producto_id():
    key = generar_key(PRODUCTO_ID, "test.pdf")
    assert key.startswith(f"prospectos/{PRODUCTO_ID}/")
    assert key.endswith("_test.pdf")
