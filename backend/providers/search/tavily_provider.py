"""
Proveedor de búsqueda usando Tavily.

TODO: Enchufar cuando haya API key.
Tier gratuito: 1000 búsquedas/mes. Registrar en https://tavily.com/

Ventajas sobre DuckDuckGo:
- API oficial con resultados más confiables
- Búsqueda de noticias recientes garantizada
- Control granular sobre dominios incluidos/excluidos
- Mejor cobertura de contenido en español

Para activar:
    1. Registrarse en https://tavily.com/
    2. Configurar TAVILY_API_KEY en .env
    3. Configurar SEARCH_PROVIDER=tavily en .env
    4. Reiniciar el servicio
"""

import logging

from models.report import ResultadoBusqueda
from providers.search.base_search import BaseSearchProvider, ProveedorBusquedaError

logger = logging.getLogger(__name__)


class TavilyProvider(BaseSearchProvider):
    """
    Proveedor de búsqueda usando la API de Tavily.

    TODO: Implementar cuando se tenga API key.
    """

    def __init__(
        self,
        api_key: str,
        max_resultados: int = 10,
        profundidad: str = "advanced",
        dominios_incluidos: list[str] | None = None,
        dominios_excluidos: list[str] | None = None,
    ) -> None:
        self._api_key = api_key
        self._max_resultados = max_resultados
        self._profundidad = profundidad
        self._dominios_incluidos = dominios_incluidos or []
        self._dominios_excluidos = dominios_excluidos or []

    async def buscar(
        self, consulta: str, max_resultados: int | None = None
    ) -> list[ResultadoBusqueda]:
        """
        TODO: Implementar búsqueda con Tavily.

        Descomentar cuando se tenga API key:

        from tavily import TavilyClient
        cliente = TavilyClient(api_key=self._api_key)
        respuesta = cliente.search(
            query=consulta,
            max_results=max_resultados or self._max_resultados,
            search_depth=self._profundidad,
            include_domains=self._dominios_incluidos,
            exclude_domains=self._dominios_excluidos,
        )
        return [
            ResultadoBusqueda(
                titulo=r["title"],
                url=r["url"],
                fragmento=r["content"],
            )
            for r in respuesta["results"]
        ]
        """
        raise NotImplementedError(
            "TavilyProvider no está implementado aún. "
            "Configurar TAVILY_API_KEY y descomentar el código en tavily_provider.py"
        )

    @property
    def nombre(self) -> str:
        return "tavily"
