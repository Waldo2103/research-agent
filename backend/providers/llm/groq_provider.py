"""
Proveedor LLM usando la API de Groq.

Groq usa hardware especializado (LPU) que ejecuta llama3 y otros modelos
a velocidades muy superiores a Ollama local — típicamente 5-10x más rápido.
Tier gratuito disponible: https://console.groq.com/

Ventajas sobre Ollama local:
- Sin necesidad de GPU ni hardware potente en el servidor
- llama-3.3-70b-versatile gratis: calidad muy superior a llama3 8B local
- Respuestas más largas y detalladas (hasta 32k tokens de contexto)
- Latencia baja incluso en CPU

Para activar:
    1. Crear cuenta en https://console.groq.com/
    2. Generar API key en Settings → API Keys
    3. En .env: LLM_PROVIDER=groq, GROQ_API_KEY=gsk_...
    4. Reiniciar: docker-compose restart backend
"""

import logging

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq

from providers.llm.base_llm import BaseLLMProvider

logger = logging.getLogger(__name__)


class ProveedorGroqError(Exception):
    """Error específico del proveedor Groq."""
    pass


class GroqProvider(BaseLLMProvider):
    """
    Proveedor LLM usando la API de Groq.

    Soporta todos los modelos disponibles en Groq, incluyendo:
    - llama-3.3-70b-versatile (recomendado — gratis, alta calidad)
    - llama3-8b-8192 (más rápido, menor calidad)
    - mixtral-8x7b-32768 (buena calidad en español)
    - gemma2-9b-it (alternativa liviana)
    """

    def __init__(
        self,
        api_key: str,
        modelo: str = "llama-3.3-70b-versatile",
        temperatura: float = 0.3,
        max_tokens: int = 8192,
    ) -> None:
        """
        Inicializa el proveedor Groq.

        Args:
            api_key: API key de Groq (obtener en console.groq.com)
            modelo: Nombre del modelo a usar
            temperatura: Temperatura de muestreo (0.0 a 1.0)
            max_tokens: Máximo de tokens en la respuesta
        """
        if not api_key:
            raise ProveedorGroqError(
                "GROQ_API_KEY no está configurada. "
                "Obtener en https://console.groq.com/ y agregar al .env"
            )

        self._api_key = api_key
        self._modelo = modelo
        self._temperatura = temperatura
        self._max_tokens = max_tokens
        self._instancia: BaseChatModel | None = None

        logger.info("GroqProvider inicializado: modelo=%s", modelo)

    def get_modelo(self) -> BaseChatModel:
        """
        Retorna la instancia de ChatGroq lista para usar.

        Usa patrón singleton para no crear múltiples instancias.

        Returns:
            Instancia de ChatGroq configurada.
        """
        if self._instancia is None:
            self._instancia = ChatGroq(
                api_key=self._api_key,
                model=self._modelo,
                temperature=self._temperatura,
                max_tokens=self._max_tokens,
            )
            logger.debug("Instancia de ChatGroq creada para modelo: %s", self._modelo)
        return self._instancia

    def esta_disponible(self) -> bool:
        """
        Verifica que la API key de Groq sea válida y el servicio esté accesible.

        Hace una llamada liviana al endpoint de modelos de Groq para
        confirmar que la API key funciona sin consumir créditos.

        Returns:
            True si Groq responde correctamente con la API key dada.
        """
        if not self._api_key or not self._api_key.startswith("gsk_"):
            logger.warning(
                "GROQ_API_KEY no tiene el formato esperado (debe empezar con 'gsk_')"
            )
            return False

        try:
            respuesta = httpx.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=10.0,
            )
            if respuesta.status_code == 200:
                modelos = [m["id"] for m in respuesta.json().get("data", [])]
                disponible = self._modelo in modelos
                if not disponible:
                    logger.warning(
                        "Modelo '%s' no encontrado en Groq. Modelos disponibles: %s",
                        self._modelo,
                        modelos,
                    )
                return disponible

            if respuesta.status_code == 401:
                logger.error("GROQ_API_KEY inválida o revocada")
                return False

            logger.warning("Groq respondió con status inesperado: %d", respuesta.status_code)
            return False

        except httpx.ConnectError:
            logger.error("No se puede conectar a la API de Groq. ¿Hay conexión a internet?")
            return False
        except httpx.TimeoutException:
            logger.error("Timeout al conectar con la API de Groq")
            return False

    @property
    def nombre(self) -> str:
        return f"groq/{self._modelo}"
