"""
Proveedor de almacenamiento usando PostgreSQL.

TODO v2: Enchufar para producción cuando el equipo crezca.
Cambiar de SQLite a Postgres = cambiar DATABASE_URL en .env.

Para activar:
    1. Configurar STORAGE_PROVIDER=postgres en .env
    2. Configurar DATABASE_URL=postgresql://usuario:contraseña@host:5432/db en .env
    3. Ejecutar migraciones: docker-compose exec backend alembic upgrade head
"""

import logging
from typing import Optional

from models.report import InformeResearch
from providers.storage.base_storage import BaseStorageProvider

logger = logging.getLogger(__name__)


class PostgresProvider(BaseStorageProvider):
    """
    Proveedor de almacenamiento usando PostgreSQL con SQLAlchemy async.

    TODO v2: Implementar. La lógica es idéntica a SQLiteProvider,
    solo cambia la connection string y el driver (asyncpg vs aiosqlite).
    """

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        logger.info("PostgresProvider inicializado: %s", database_url.split("@")[-1])

    async def guardar_informe(self, informe: InformeResearch) -> str:
        raise NotImplementedError(
            "PostgresProvider.guardar_informe() no está implementado (TODO v2)"
        )

    async def obtener_informe(self, informe_id: str) -> Optional[InformeResearch]:
        raise NotImplementedError(
            "PostgresProvider.obtener_informe() no está implementado (TODO v2)"
        )

    async def listar_informes(self, limite: int = 50) -> list[InformeResearch]:
        raise NotImplementedError(
            "PostgresProvider.listar_informes() no está implementado (TODO v2)"
        )

    @property
    def nombre(self) -> str:
        return "postgres"
