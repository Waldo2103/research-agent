"""
Tool de búsqueda web para el agente LangChain.

Envuelve el SearchProvider en un formato compatible con LangChain tools,
aunque en la implementación actual el agente llama al provider directamente
para mayor control sobre el flujo de búsquedas múltiples en paralelo.
"""

import logging
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from providers.search.base_search import BaseSearchProvider

logger = logging.getLogger(__name__)


class EntradaBusqueda(BaseModel):
    """Schema de entrada para la herramienta de búsqueda."""

    consulta: str = Field(
        ...,
        description="La consulta de búsqueda web en español",
    )


class SearchTool(BaseTool):
    """
    Herramienta de búsqueda web para el agente LangChain.

    Permite al agente buscar información en la web usando
    el proveedor configurado (DuckDuckGo, Tavily, etc.)
    """

    name: str = "busqueda_web"
    description: str = (
        "Busca información en la web sobre un tema. "
        "Úsala para encontrar noticias, artículos y datos sobre cualquier tema. "
        "Input: una consulta de búsqueda en español."
    )
    args_schema: Type[BaseModel] = EntradaBusqueda

    # El provider se inyecta desde afuera — no hardcodeado
    proveedor: BaseSearchProvider = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, consulta: str) -> str:
        """
        Ejecución síncrona (requerida por BaseTool).
        En la práctica usamos _arun para async.
        """
        import asyncio
        return asyncio.run(self._arun(consulta))

    async def _arun(self, consulta: str) -> str:
        """
        Ejecuta la búsqueda de forma asíncrona.

        Args:
            consulta: La consulta de búsqueda

        Returns:
            Resultados formateados como texto para el LLM
        """
        logger.info("SearchTool ejecutando: '%s'", consulta)
        resultados = await self.proveedor.buscar(consulta)

        if not resultados:
            return f"No se encontraron resultados para: {consulta}"

        # Formatear resultados para el LLM
        lineas = []
        for i, r in enumerate(resultados, 1):
            lineas.append(f"[{i}] {r.titulo}")
            lineas.append(f"    URL: {r.url}")
            lineas.append(f"    {r.fragmento}")
            lineas.append("")

        return "\n".join(lineas)


def crear_search_tool(proveedor: BaseSearchProvider) -> SearchTool:
    """
    Factory para crear un SearchTool con el proveedor inyectado.

    Args:
        proveedor: La instancia del proveedor de búsqueda

    Returns:
        Instancia de SearchTool lista para usar en el agente
    """
    return SearchTool(proveedor=proveedor)
