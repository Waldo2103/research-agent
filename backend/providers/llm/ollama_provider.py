"""
Proveedor LLM usando Ollama (modelos locales, gratis).

Ollama permite correr modelos como llama3, mistral, mixtral
completamente offline en el servidor local.
"""

import logging

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from providers.llm.base_llm import BaseLLMProvider

logger = logging.getLogger(__name__)


class ProveedorOllamaError(Exception):
    """Error específico del proveedor Ollama."""
    pass


class OllamaProvider(BaseLLMProvider):
    """
    Proveedor LLM usando Ollama para inferencia local.

    Usa ChatOllama de LangChain como interfaz al servidor Ollama.
    Compatible con llama3, mistral, mixtral y cualquier modelo
    disponible en la librería de Ollama.
    """

    def __init__(
        self,
        base_url: str,
        modelo: str,
        temperatura: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        """
        Inicializa el proveedor Ollama.

        Args:
            base_url: URL del servidor Ollama (ej: http://ollama:11434)
            modelo: Nombre del modelo a usar (ej: llama3, mistral)
            temperatura: Temperatura de muestreo (0.0 a 1.0)
            max_tokens: Máximo de tokens en la respuesta
        """
        self._base_url = base_url
        self._modelo = modelo
        self._temperatura = temperatura
        self._max_tokens = max_tokens
        self._instancia: BaseChatModel | None = None

        logger.info(
            "OllamaProvider inicializado: modelo=%s, url=%s", modelo, base_url
        )

    def get_modelo(self) -> BaseChatModel:
        """
        Retorna la instancia de ChatOllama lista para usar.

        Usa patrón singleton para no crear múltiples instancias.

        Returns:
            Instancia de ChatOllama configurada.
        """
        if self._instancia is None:
            self._instancia = ChatOllama(
                base_url=self._base_url,
                model=self._modelo,
                temperature=self._temperatura,
                num_predict=self._max_tokens,
            )
            logger.debug("Instancia de ChatOllama creada para modelo: %s", self._modelo)
        return self._instancia

    def esta_disponible(self) -> bool:
        """
        Verifica que el servidor Ollama esté accesible y el modelo descargado.

        Returns:
            True si Ollama responde y el modelo está disponible.
        """
        try:
            respuesta = httpx.get(f"{self._base_url}/api/tags", timeout=5.0)
            if respuesta.status_code != 200:
                logger.warning(
                    "Ollama respondió con status %d", respuesta.status_code
                )
                return False

            modelos_disponibles = [
                m["name"] for m in respuesta.json().get("models", [])
            ]
            # Verificar si el modelo base está descargado (ej: "llama3" en "llama3:latest")
            modelo_base = self._modelo.split(":")[0]
            disponible = any(modelo_base in m for m in modelos_disponibles)

            if not disponible:
                logger.warning(
                    "Modelo '%s' no encontrado en Ollama. Modelos disponibles: %s",
                    self._modelo,
                    modelos_disponibles,
                )
            return disponible

        except httpx.ConnectError:
            logger.error(
                "No se puede conectar a Ollama en %s. ¿Está corriendo el servicio?",
                self._base_url,
            )
            return False
        except httpx.TimeoutException:
            logger.error("Timeout al conectar a Ollama en %s", self._base_url)
            return False

    @property
    def nombre(self) -> str:
        return f"ollama/{self._modelo}"
