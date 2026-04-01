"""
Proveedor de búsqueda usando Tavily.

Tier gratuito: 1000 búsquedas/mes. Registrar en https://tavily.com/
"""

import logging
from datetime import datetime

from tavily import AsyncTavilyClient

from models.report import ResultadoBusqueda
from providers.search.base_search import BaseSearchProvider, ProveedorBusquedaError

logger = logging.getLogger(__name__)


class TavilyProvider(BaseSearchProvider):
    """Proveedor de búsqueda usando la API de Tavily."""

    def __init__(
        self,
        api_key: str,
        max_resultados: int = 10,
        profundidad: str = "advanced",
        dominios_incluidos: list[str] | None = None,
        dominios_excluidos: list[str] | None = None,
    ) -> None:
        if not api_key:
            raise ProveedorBusquedaError(
                proveedor="tavily",
                mensaje="TAVILY_API_KEY no está configurada en .env",
            )
        self._max_resultados = max_resultados
        self._profundidad = profundidad
        self._dominios_incluidos = dominios_incluidos or []
        self._dominios_excluidos = dominios_excluidos or []
        self._cliente = AsyncTavilyClient(api_key=api_key)

        logger.info(
            "TavilyProvider inicializado: profundidad=%s, max_resultados=%d",
            profundidad,
            max_resultados,
        )

    async def buscar(
        self, consulta: str, max_resultados: int | None = None
    ) -> list[ResultadoBusqueda]:
        """Ejecuta una búsqueda en Tavily y retorna los resultados."""
        limite = max_resultados or self._max_resultados
        fecha_consulta = datetime.now()

        logger.info("Tavily buscando: '%s' (max: %d)", consulta, limite)

        try:
            respuesta = await self._cliente.search(
                query=consulta,
                max_results=limite,
                search_depth=self._profundidad,
                include_domains=self._dominios_incluidos or None,
                exclude_domains=self._dominios_excluidos or None,
            )

            resultados = [
                ResultadoBusqueda(
                    titulo=r.get("title", "Sin título"),
                    url=r.get("url", ""),
                    fragmento=r.get("content", ""),
                    fecha_consulta=fecha_consulta,
                )
                for r in respuesta.get("results", [])
                if r.get("url")
            ]

            logger.info(
                "Tavily retornó %d resultados para '%s'",
                len(resultados),
                consulta,
            )
            return resultados

        except Exception as e:
            raise ProveedorBusquedaError(
                proveedor=self.nombre,
                mensaje=f"Error en búsqueda de Tavily: {e}",
            ) from e

    @property
    def nombre(self) -> str:
        return "tavily"
