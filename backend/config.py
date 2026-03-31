"""
Configuración centralizada del agente de research.

Lee todas las variables de entorno y provee:
1. Configuración tipada via Pydantic Settings
2. Factories que retornan la instancia correcta de cada proveedor

Principio: cambiar de proveedor = cambiar variable en .env, no tocar código.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN TIPADA CON PYDANTIC SETTINGS
# ─────────────────────────────────────────────────────────────────────────────


class Configuracion(BaseSettings):
    """
    Todas las variables de configuración del sistema.

    Se leen automáticamente desde el archivo .env o variables de entorno.
    """

    # General
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_port: int = Field(default=8000, alias="API_PORT")
    secret_key: str = Field(default="clave-secreta-dev", alias="SECRET_KEY")
    cors_origins: str = Field(
        default="http://localhost,http://localhost:3000", alias="CORS_ORIGINS"
    )

    # LLM
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")

    # Ollama
    ollama_base_url: str = Field(
        default="http://ollama:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="llama3", alias="OLLAMA_MODEL")

    # OpenAI (TODO)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Anthropic (TODO)
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514", alias="ANTHROPIC_MODEL"
    )

    # Groq
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    groq_temperature: float = Field(default=0.3, alias="GROQ_TEMPERATURE")
    groq_max_tokens: int = Field(default=8192, alias="GROQ_MAX_TOKENS")

    # Búsqueda
    search_provider: str = Field(default="duckduckgo", alias="SEARCH_PROVIDER")
    search_max_results: int = Field(default=10, alias="SEARCH_MAX_RESULTS")
    search_delay_seconds: float = Field(default=1.0, alias="SEARCH_DELAY_SECONDS")
    search_region: str = Field(default="ar-es", alias="SEARCH_REGION")
    search_safesearch: str = Field(default="off", alias="SEARCH_SAFESEARCH")

    # Tavily (TODO)
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    tavily_search_depth: str = Field(default="advanced", alias="TAVILY_SEARCH_DEPTH")

    # Vector store
    vector_provider: str = Field(default="chroma", alias="VECTOR_PROVIDER")
    chroma_persist_dir: str = Field(
        default="/app/data/chroma", alias="CHROMA_PERSIST_DIR"
    )
    chroma_collection_name: str = Field(
        default="research_agent", alias="CHROMA_COLLECTION_NAME"
    )

    # Storage (TODO v2)
    storage_provider: str = Field(default="sqlite", alias="STORAGE_PROVIDER")
    database_url: str = Field(
        default="sqlite:///./data/db/research_agent.db", alias="DATABASE_URL"
    )

    # PDF
    pdf_provider: str = Field(default="weasyprint", alias="PDF_PROVIDER")
    pdf_output_dir: str = Field(default="/app/data/pdfs", alias="PDF_OUTPUT_DIR")

    # Agente
    agent_max_searches: int = Field(default=5, alias="AGENT_MAX_SEARCHES")
    agent_max_iterations: int = Field(default=10, alias="AGENT_MAX_ITERATIONS")
    agent_timeout_seconds: int = Field(default=120, alias="AGENT_TIMEOUT_SECONDS")
    agent_context_results: int = Field(default=5, alias="AGENT_CONTEXT_RESULTS")

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}


@lru_cache(maxsize=1)
def obtener_config() -> Configuracion:
    """
    Retorna la instancia única de configuración (singleton).

    Usa lru_cache para no releer el .env en cada llamada.
    """
    return Configuracion()


# ─────────────────────────────────────────────────────────────────────────────
# FACTORIES DE PROVEEDORES
# ─────────────────────────────────────────────────────────────────────────────


def get_llm_provider():
    """
    Factory que retorna el proveedor LLM configurado en .env.

    Proveedor activo por defecto: ollama
    Para cambiar: modificar LLM_PROVIDER en .env

    Returns:
        Instancia de BaseLLMProvider

    Raises:
        ValueError: Si el proveedor configurado no es reconocido
    """
    config = obtener_config()
    proveedor = config.llm_provider.lower()

    logger.info("Inicializando proveedor LLM: %s", proveedor)

    if proveedor == "ollama":
        from providers.llm.ollama_provider import OllamaProvider
        return OllamaProvider(
            base_url=config.ollama_base_url,
            modelo=config.ollama_model,
            temperatura=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
        )

    elif proveedor == "openai":
        from providers.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=config.openai_api_key,
            modelo=config.openai_model,
            temperatura=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
        )

    elif proveedor == "anthropic":
        from providers.llm.openai_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=config.anthropic_api_key,
            modelo=config.anthropic_model,
            temperatura=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
        )

    elif proveedor == "groq":
        from providers.llm.groq_provider import GroqProvider
        return GroqProvider(
            api_key=config.groq_api_key,
            modelo=config.groq_model,
            temperatura=config.groq_temperature,
            max_tokens=config.groq_max_tokens,
        )

    else:
        raise ValueError(
            f"Proveedor LLM desconocido: '{proveedor}'. "
            f"Opciones válidas: ollama, openai, anthropic, groq"
        )


def get_search_provider():
    """
    Factory que retorna el proveedor de búsqueda configurado en .env.

    Proveedor activo por defecto: duckduckgo
    Para cambiar: modificar SEARCH_PROVIDER en .env

    Returns:
        Instancia de BaseSearchProvider

    Raises:
        ValueError: Si el proveedor configurado no es reconocido
    """
    config = obtener_config()
    proveedor = config.search_provider.lower()

    logger.info("Inicializando proveedor de búsqueda: %s", proveedor)

    if proveedor == "duckduckgo":
        from providers.search.duckduckgo_provider import DuckDuckGoProvider
        return DuckDuckGoProvider(
            max_resultados=config.search_max_results,
            region=config.search_region,
            safesearch=config.search_safesearch,
            delay_segundos=config.search_delay_seconds,
        )

    elif proveedor == "tavily":
        from providers.search.tavily_provider import TavilyProvider
        return TavilyProvider(
            api_key=config.tavily_api_key,
            max_resultados=config.search_max_results,
            profundidad=config.tavily_search_depth,
        )

    else:
        raise ValueError(
            f"Proveedor de búsqueda desconocido: '{proveedor}'. "
            f"Opciones válidas: duckduckgo, tavily"
        )


def get_storage_provider():
    """
    Factory que retorna el proveedor de almacenamiento configurado en .env.

    TODO v2: Implementar SQLiteProvider y PostgresProvider.

    Returns:
        Instancia de BaseStorageProvider

    Raises:
        ValueError: Si el proveedor configurado no es reconocido
    """
    config = obtener_config()
    proveedor = config.storage_provider.lower()

    logger.info("Inicializando proveedor de storage: %s", proveedor)

    if proveedor == "sqlite":
        from providers.storage.sqlite_provider import SQLiteProvider
        return SQLiteProvider(database_url=config.database_url)

    elif proveedor == "postgres":
        from providers.storage.postgres_provider import PostgresProvider
        return PostgresProvider(database_url=config.database_url)

    else:
        raise ValueError(
            f"Proveedor de storage desconocido: '{proveedor}'. "
            f"Opciones válidas: sqlite, postgres"
        )


def configurar_logging() -> None:
    """Configura el sistema de logging basado en LOG_LEVEL del .env."""
    config = obtener_config()
    nivel = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def asegurar_directorios() -> None:
    """Crea los directorios de datos necesarios si no existen."""
    config = obtener_config()
    for directorio in [config.pdf_output_dir, config.chroma_persist_dir]:
        Path(directorio).mkdir(parents=True, exist_ok=True)
        logger.debug("Directorio asegurado: %s", directorio)
