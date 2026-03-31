"""
Interfaz abstracta para proveedores de LLM.

Todos los proveedores concretos deben implementar esta clase.
El agente solo depende de BaseLLMProvider, nunca de implementaciones concretas.
"""

from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel


class BaseLLMProvider(ABC):
    """
    Interfaz base para todos los proveedores de modelo de lenguaje.

    Principio de uso: el agente recibe una instancia de BaseLLMProvider
    y llama a get_modelo() para obtener el LLM de LangChain. De esta
    manera, cambiar de Ollama a OpenAI no requiere modificar el agente.
    """

    @abstractmethod
    def get_modelo(self) -> BaseChatModel:
        """
        Retorna la instancia del modelo de LangChain lista para usar.

        Returns:
            Una instancia de BaseChatModel (ChatOllama, ChatOpenAI, etc.)
        """
        ...

    @abstractmethod
    def esta_disponible(self) -> bool:
        """
        Verifica si el proveedor está disponible y correctamente configurado.

        Returns:
            True si el proveedor puede recibir solicitudes, False en caso contrario.
        """
        ...

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre identificador del proveedor (para logging)."""
        ...
