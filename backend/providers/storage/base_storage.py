"""
Interfaz abstracta para proveedores de almacenamiento.

Define las operaciones de historial de informes.
Implementación activa: TODO v2 (SQLite / PostgreSQL).
"""

from abc import ABC, abstractmethod
from typing import Optional

from models.report import InformeResearch


class BaseStorageProvider(ABC):
    """
    Interfaz base para proveedores de almacenamiento de informes.

    TODO v2: Implementar SQLiteProvider y PostgresProvider.
    """

    @abstractmethod
    async def guardar_informe(self, informe: InformeResearch) -> str:
        """
        Persiste un informe en el almacenamiento.

        Args:
            informe: El informe a guardar.

        Returns:
            El ID del informe guardado.
        """
        ...

    @abstractmethod
    async def obtener_informe(self, informe_id: str) -> Optional[InformeResearch]:
        """
        Recupera un informe por su ID.

        Args:
            informe_id: El identificador único del informe.

        Returns:
            El informe si existe, None en caso contrario.
        """
        ...

    @abstractmethod
    async def listar_informes(self, limite: int = 50) -> list[InformeResearch]:
        """
        Lista los informes guardados, del más reciente al más antiguo.

        Args:
            limite: Número máximo de informes a retornar.

        Returns:
            Lista de informes ordenados por fecha de creación descendente.
        """
        ...

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre identificador del proveedor (para logging)."""
        ...


class ProveedorStorageError(Exception):
    """Error específico para fallos en el proveedor de almacenamiento."""

    def __init__(self, proveedor: str, mensaje: str) -> None:
        self.proveedor = proveedor
        super().__init__(f"[{proveedor}] Error de almacenamiento: {mensaje}")
