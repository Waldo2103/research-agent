"""
Tests unitarios para el proveedor DuckDuckGo.

Usa mocks para no hacer llamadas reales a la red durante los tests.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from providers.search.duckduckgo_provider import DuckDuckGoProvider
from providers.search.base_search import ProveedorBusquedaError


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def proveedor():
    """Instancia de DuckDuckGoProvider con configuración mínima para tests."""
    return DuckDuckGoProvider(
        max_resultados=5,
        region="ar-es",
        safesearch="off",
        delay_segundos=0.0,  # Sin delay en tests
    )


RESULTADOS_MOCK = [
    {
        "title": "Resultado de prueba 1",
        "href": "https://ejemplo.com/1",
        "body": "Fragmento del primer resultado de prueba.",
    },
    {
        "title": "Resultado de prueba 2",
        "href": "https://ejemplo.com/2",
        "body": "Fragmento del segundo resultado de prueba.",
    },
    {
        "title": "Sin URL",
        "href": "",   # Debe ser filtrado
        "body": "Este resultado no tiene URL y debe ser ignorado.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_buscar_retorna_lista_de_resultados(proveedor):
    """buscar() debe retornar una lista de ResultadoBusqueda."""
    with patch.object(proveedor, "_buscar_sincrono", return_value=RESULTADOS_MOCK):
        resultados = await proveedor.buscar("test query")

    assert isinstance(resultados, list)
    assert len(resultados) == 2  # El resultado sin URL debe ser filtrado


@pytest.mark.asyncio
async def test_buscar_filtra_resultados_sin_url(proveedor):
    """buscar() debe ignorar resultados que no tienen URL."""
    with patch.object(proveedor, "_buscar_sincrono", return_value=RESULTADOS_MOCK):
        resultados = await proveedor.buscar("test query")

    urls = [r.url for r in resultados]
    assert "" not in urls
    assert all(url.startswith("http") for url in urls)


@pytest.mark.asyncio
async def test_buscar_mapea_campos_correctamente(proveedor):
    """buscar() debe mapear title, href y body a los campos correctos."""
    with patch.object(proveedor, "_buscar_sincrono", return_value=RESULTADOS_MOCK[:1]):
        resultados = await proveedor.buscar("test query")

    resultado = resultados[0]
    assert resultado.titulo == "Resultado de prueba 1"
    assert resultado.url == "https://ejemplo.com/1"
    assert resultado.fragmento == "Fragmento del primer resultado de prueba."
    assert isinstance(resultado.fecha_consulta, datetime)


@pytest.mark.asyncio
async def test_buscar_retorna_lista_vacia_cuando_no_hay_resultados(proveedor):
    """buscar() debe retornar lista vacía si DuckDuckGo no encuentra nada."""
    with patch.object(proveedor, "_buscar_sincrono", return_value=[]):
        resultados = await proveedor.buscar("xkzqwrty consulta inexistente")

    assert resultados == []


@pytest.mark.asyncio
async def test_buscar_lanza_error_cuando_ddg_falla(proveedor):
    """buscar() debe lanzar ProveedorBusquedaError si DuckDuckGo falla."""
    from ddgs.exceptions import DDGSException

    with patch.object(
        proveedor,
        "_buscar_sincrono",
        side_effect=DDGSException("Rate limit"),
    ):
        with pytest.raises(ProveedorBusquedaError) as exc_info:
            await proveedor.buscar("test query")

    assert "duckduckgo" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_buscar_respeta_max_resultados(proveedor):
    """buscar() debe pasar el límite correcto a _buscar_sincrono."""
    resultados_raw = [
        {"title": f"Resultado {i}", "href": f"https://ejemplo.com/{i}", "body": "texto"}
        for i in range(10)
    ]

    llamadas_limite = []

    def mock_buscar(consulta, limite):
        llamadas_limite.append(limite)
        return resultados_raw[:limite]

    with patch.object(proveedor, "_buscar_sincrono", side_effect=mock_buscar):
        await proveedor.buscar("test query", max_resultados=3)

    assert llamadas_limite[0] == 3


def test_nombre_del_proveedor(proveedor):
    """nombre debe retornar 'duckduckgo'."""
    assert proveedor.nombre == "duckduckgo"
