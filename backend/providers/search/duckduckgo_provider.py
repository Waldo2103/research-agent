"""
Proveedor de búsqueda usando DuckDuckGo.

No requiere API key. Usa la librería ddgs (ex duckduckgo-search)
que hace scraping de la interfaz web de DuckDuckGo.
"""

import asyncio
import logging
from datetime import datetime

from ddgs import DDGS
from ddgs.exceptions import DDGSException

from models.report import ResultadoBusqueda
from providers.search.base_search import BaseSearchProvider, ProveedorBusquedaError

logger = logging.getLogger(__name__)


class DuckDuckGoProvider(BaseSearchProvider):
    """
    Proveedor de búsqueda usando DuckDuckGo (sin API key, gratis).

    Limitaciones conocidas:
    - Sin garantía de resultados de noticias muy recientes
    - Puede ser bloqueado temporalmente con muchas consultas seguidas
      (mitigar con SEARCH_DELAY_SECONDS en .env)
    - Sin control granular sobre la cantidad de resultados
    """

    def __init__(
        self,
        max_resultados: int = 10,
        region: str = "ar-es",
        safesearch: str = "off",
        delay_segundos: float = 1.0,
    ) -> None:
        """
        Inicializa el proveedor DuckDuckGo.

        Args:
            max_resultados: Número máximo de resultados por búsqueda
            region: Región para resultados locales (ar-es, es-es, wt-wt)
            safesearch: Filtro de contenido (off, moderate, strict)
            delay_segundos: Espera entre búsquedas para evitar rate limiting
        """
        self._max_resultados = max_resultados
        self._region = region
        self._safesearch = safesearch
        self._delay_segundos = delay_segundos

        logger.info(
            "DuckDuckGoProvider inicializado: region=%s, max_resultados=%d",
            region,
            max_resultados,
        )

    async def buscar(
        self, consulta: str, max_resultados: int | None = None
    ) -> list[ResultadoBusqueda]:
        """
        Ejecuta una búsqueda en DuckDuckGo y retorna los resultados.

        La librería duckduckgo-search es síncrona, por lo que usamos
        asyncio.to_thread para no bloquear el event loop de FastAPI.

        Args:
            consulta: La consulta de búsqueda
            max_resultados: Sobreescribe el máximo por defecto si se provee

        Returns:
            Lista de ResultadoBusqueda

        Raises:
            ProveedorBusquedaError: Si la búsqueda falla
        """
        limite = max_resultados or self._max_resultados
        fecha_consulta = datetime.now()

        logger.info("DuckDuckGo buscando: '%s' (max: %d)", consulta, limite)
        inicio = asyncio.get_event_loop().time()

        try:
            # Ejecutar búsqueda síncrona en un thread separado
            resultados_raw = await asyncio.to_thread(
                self._buscar_sincrono, consulta, limite
            )

            resultados = [
                ResultadoBusqueda(
                    titulo=r.get("title", "Sin título"),
                    url=r.get("href", ""),
                    fragmento=r.get("body", ""),
                    fecha_consulta=fecha_consulta,
                )
                for r in resultados_raw
                if r.get("href")  # Filtrar resultados sin URL
            ]

            duracion = asyncio.get_event_loop().time() - inicio
            logger.info(
                "DuckDuckGo retornó %d resultados para '%s' en %.2fs",
                len(resultados),
                consulta,
                duracion,
            )

            # Pausa para evitar rate limiting en búsquedas consecutivas
            if self._delay_segundos > 0:
                await asyncio.sleep(self._delay_segundos)

            return resultados

        except DDGSException as e:
            raise ProveedorBusquedaError(
                proveedor=self.nombre,
                mensaje=f"Error en búsqueda de DuckDuckGo: {e}",
            ) from e

    def _buscar_sincrono(self, consulta: str, limite: int) -> list[dict]:
        """
        Ejecuta la búsqueda de forma síncrona (llamado desde asyncio.to_thread).

        Args:
            consulta: La consulta de búsqueda
            limite: Número máximo de resultados

        Returns:
            Lista de resultados crudos de DuckDuckGo
        """
        with DDGS() as ddgs:
            return list(
                ddgs.text(
                    consulta,
                    max_results=limite,
                    region=self._region,
                    safesearch=self._safesearch,
                )
            )

    @property
    def nombre(self) -> str:
        return "duckduckgo"
