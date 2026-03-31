"""
Interfaz abstracta para proveedores de búsqueda web.

Todos los proveedores concretos (DuckDuckGo, Tavily, etc.) deben implementar esta clase.
"""

from abc import ABC, abstractmethod

from models.report import ResultadoBusqueda


class BaseSearchProvider(ABC):
    """
    Interfaz base para todos los proveedores de búsqueda web.

    El agente usa esta interfaz para buscar información sin conocer
    el proveedor subyacente (DuckDuckGo, Tavily, SerpAPI, etc.).
    """

    @abstractmethod
    async def buscar(
        self, consulta: str, max_resultados: int = 10
    ) -> list[ResultadoBusqueda]:
        """
        Ejecuta una búsqueda web y retorna los resultados.

        Args:
            consulta: La consulta de búsqueda en texto libre.
            max_resultados: Número máximo de resultados a retornar.

        Returns:
            Lista de ResultadoBusqueda ordenados por relevancia.

        Raises:
            ProveedorBusquedaError: Si la búsqueda falla.
        """
        ...

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre identificador del proveedor (para logging)."""
        ...


class ProveedorBusquedaError(Exception):
    """Error específico para fallos en el proveedor de búsqueda."""

    def __init__(self, proveedor: str, mensaje: str) -> None:
        self.proveedor = proveedor
        super().__init__(f"[{proveedor}] Error de búsqueda: {mensaje}")
