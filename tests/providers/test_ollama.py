"""
Tests unitarios para el proveedor Ollama.

Usa mocks para no requerir un servidor Ollama corriendo durante los tests.
"""

import pytest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from providers.llm.ollama_provider import OllamaProvider


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def proveedor():
    """Instancia de OllamaProvider con configuración de tests."""
    return OllamaProvider(
        base_url="http://localhost:11434",
        modelo="llama3",
        temperatura=0.3,
        max_tokens=4096,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_get_modelo_retorna_instancia_de_chat_ollama(proveedor):
    """get_modelo() debe retornar una instancia de ChatOllama."""
    from langchain_ollama import ChatOllama

    modelo = proveedor.get_modelo()

    assert isinstance(modelo, ChatOllama)


def test_get_modelo_usa_singleton(proveedor):
    """get_modelo() debe retornar siempre la misma instancia."""
    modelo_1 = proveedor.get_modelo()
    modelo_2 = proveedor.get_modelo()

    assert modelo_1 is modelo_2


def test_nombre_del_proveedor(proveedor):
    """nombre debe incluir el proveedor y el modelo."""
    assert proveedor.nombre == "ollama/llama3"


def test_esta_disponible_retorna_true_cuando_ollama_responde(proveedor):
    """esta_disponible() debe retornar True si Ollama responde con el modelo."""
    respuesta_mock = MagicMock()
    respuesta_mock.status_code = 200
    respuesta_mock.json.return_value = {
        "models": [{"name": "llama3:latest"}]
    }

    with patch("httpx.get", return_value=respuesta_mock):
        disponible = proveedor.esta_disponible()

    assert disponible is True


def test_esta_disponible_retorna_false_cuando_modelo_no_descargado(proveedor):
    """esta_disponible() debe retornar False si el modelo no está en Ollama."""
    respuesta_mock = MagicMock()
    respuesta_mock.status_code = 200
    respuesta_mock.json.return_value = {
        "models": [{"name": "mistral:latest"}]  # llama3 no está
    }

    with patch("httpx.get", return_value=respuesta_mock):
        disponible = proveedor.esta_disponible()

    assert disponible is False


def test_esta_disponible_retorna_false_cuando_ollama_no_responde(proveedor):
    """esta_disponible() debe retornar False si no puede conectarse a Ollama."""
    import httpx

    with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
        disponible = proveedor.esta_disponible()

    assert disponible is False


def test_esta_disponible_retorna_false_en_timeout(proveedor):
    """esta_disponible() debe retornar False si Ollama tarda demasiado."""
    import httpx

    with patch("httpx.get", side_effect=httpx.TimeoutException("Timeout")):
        disponible = proveedor.esta_disponible()

    assert disponible is False


def test_get_modelo_configura_temperatura_correctamente():
    """get_modelo() debe configurar la temperatura especificada."""
    from langchain_ollama import ChatOllama

    proveedor = OllamaProvider(
        base_url="http://localhost:11434",
        modelo="mistral",
        temperatura=0.7,
        max_tokens=2048,
    )
    modelo = proveedor.get_modelo()

    assert isinstance(modelo, ChatOllama)
    assert modelo.temperature == 0.7
