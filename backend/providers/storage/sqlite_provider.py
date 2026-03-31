"""
Proveedor de almacenamiento usando SQLite.

TODO v2: Implementar historial de informes.
El esquema de base de datos (InformeDB) ya está definido en models/report.py.

Para activar:
    1. Configurar STORAGE_PROVIDER=sqlite en .env
    2. Configurar DATABASE_URL=sqlite:///./data/db/research_agent.db en .env
    3. El proveedor creará la base de datos automáticamente al iniciar
"""

import logging
from typing import Optional

from models.report import InformeResearch
from providers.storage.base_storage import BaseStorageProvider, ProveedorStorageError

logger = logging.getLogger(__name__)


class SQLiteProvider(BaseStorageProvider):
    """
    Proveedor de almacenamiento usando SQLite con SQLAlchemy.

    TODO v2: Implementar todas las operaciones CRUD.
    """

    def __init__(self, database_url: str) -> None:
        """
        Inicializa el proveedor SQLite.

        Args:
            database_url: URL de conexión SQLite
                         (ej: sqlite:///./data/db/research_agent.db)
        """
        self._database_url = database_url
        logger.info("SQLiteProvider inicializado: %s", database_url)

    async def guardar_informe(self, informe: InformeResearch) -> str:
        """
        TODO v2: Persistir el informe en SQLite.

        Implementación pendiente:
        - Serializar campos de lista/dict a JSON
        - Insertar en tabla 'informes' via SQLAlchemy
        - Retornar el ID del informe guardado
        """
        raise NotImplementedError(
            "SQLiteProvider.guardar_informe() no está implementado (TODO v2)"
        )

    async def obtener_informe(self, informe_id: str) -> Optional[InformeResearch]:
        """
        TODO v2: Recuperar un informe por ID desde SQLite.
        """
        raise NotImplementedError(
            "SQLiteProvider.obtener_informe() no está implementado (TODO v2)"
        )

    async def listar_informes(self, limite: int = 50) -> list[InformeResearch]:
        """
        TODO v2: Listar los informes guardados en SQLite.
        """
        raise NotImplementedError(
            "SQLiteProvider.listar_informes() no está implementado (TODO v2)"
        )

    @property
    def nombre(self) -> str:
        return "sqlite"
