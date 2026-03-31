"""
Proveedor LLM usando la API de OpenAI.

TODO: Enchufar cuando haya presupuesto.
Para activar: cambiar LLM_PROVIDER=openai en .env y configurar OPENAI_API_KEY.
"""

import logging

from langchain_core.language_models import BaseChatModel

from providers.llm.base_llm import BaseLLMProvider

logger = logging.getLogger(__name__)


class ProveedorOpenAIError(Exception):
    """Error específico del proveedor OpenAI."""
    pass


class OpenAIProvider(BaseLLMProvider):
    """
    Proveedor LLM usando la API de OpenAI.

    TODO: Implementar cuando se tenga API key.
    Soporta: gpt-4o, gpt-4o-mini, gpt-3.5-turbo.

    Para activar:
        1. Configurar OPENAI_API_KEY en .env
        2. Configurar LLM_PROVIDER=openai en .env
        3. Reiniciar el servicio
    """

    def __init__(
        self,
        api_key: str,
        modelo: str = "gpt-4o-mini",
        temperatura: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        self._api_key = api_key
        self._modelo = modelo
        self._temperatura = temperatura
        self._max_tokens = max_tokens
        self._instancia: BaseChatModel | None = None

    def get_modelo(self) -> BaseChatModel:
        """
        Retorna la instancia de ChatOpenAI.

        TODO: Descomentar cuando langchain-openai esté configurado.
        """
        # TODO: Descomentar para activar OpenAI
        # from langchain_openai import ChatOpenAI
        # if self._instancia is None:
        #     self._instancia = ChatOpenAI(
        #         api_key=self._api_key,
        #         model=self._modelo,
        #         temperature=self._temperatura,
        #         max_tokens=self._max_tokens,
        #     )
        # return self._instancia
        raise NotImplementedError(
            "OpenAIProvider no está implementado aún. "
            "Configurar OPENAI_API_KEY y descomentar el código en openai_provider.py"
        )

    def esta_disponible(self) -> bool:
        """Verifica que la API key de OpenAI esté configurada."""
        return bool(self._api_key and self._api_key.startswith("sk-"))

    @property
    def nombre(self) -> str:
        return f"openai/{self._modelo}"


class AnthropicProvider(BaseLLMProvider):
    """
    Proveedor LLM usando la API de Anthropic (Claude).

    TODO: Implementar cuando se tenga API key.
    Soporta: claude-sonnet-4-20250514, claude-opus-4-6, claude-haiku-4-5-20251001.

    Para activar:
        1. Configurar ANTHROPIC_API_KEY en .env
        2. Configurar LLM_PROVIDER=anthropic en .env
        3. Reiniciar el servicio
    """

    def __init__(
        self,
        api_key: str,
        modelo: str = "claude-sonnet-4-20250514",
        temperatura: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        self._api_key = api_key
        self._modelo = modelo
        self._temperatura = temperatura
        self._max_tokens = max_tokens
        self._instancia: BaseChatModel | None = None

    def get_modelo(self) -> BaseChatModel:
        """
        Retorna la instancia de ChatAnthropic.

        TODO: Descomentar cuando langchain-anthropic esté configurado.
        """
        # TODO: Descomentar para activar Anthropic
        # from langchain_anthropic import ChatAnthropic
        # if self._instancia is None:
        #     self._instancia = ChatAnthropic(
        #         api_key=self._api_key,
        #         model=self._modelo,
        #         temperature=self._temperatura,
        #         max_tokens=self._max_tokens,
        #     )
        # return self._instancia
        raise NotImplementedError(
            "AnthropicProvider no está implementado aún. "
            "Configurar ANTHROPIC_API_KEY y descomentar el código en openai_provider.py"
        )

    def esta_disponible(self) -> bool:
        return bool(self._api_key and self._api_key.startswith("sk-ant-"))

    @property
    def nombre(self) -> str:
        return f"anthropic/{self._modelo}"


# GroqProvider fue movido a groq_provider.py (implementación completa).
