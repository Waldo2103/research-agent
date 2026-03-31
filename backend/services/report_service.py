"""
Servicio orquestador de generación de informes.

Coordina el agente de investigación y el servicio de PDF.
Es el punto de entrada principal para la capa de API (main.py).
"""

import logging
import time
from pathlib import Path

from agent.research_agent import AgenteResearch, AgentError
from config import get_llm_provider, get_search_provider, obtener_config
from models.report import InformeResearch
from services.pdf_service import PDFService, GeneracionPDFError

logger = logging.getLogger(__name__)


class ReportService:
    """
    Orquesta la generación completa de un informe de investigación.

    Responsabilidades:
    1. Coordinar el agente de investigación
    2. Generar el PDF del informe
    3. Adjuntar la URL de descarga del PDF al informe
    4. TODO v2: Persistir el informe en el storage provider
    """

    def __init__(self) -> None:
        """Inicializa el servicio con los proveedores configurados en .env"""
        config = obtener_config()

        self._llm_provider = get_llm_provider()
        self._search_provider = get_search_provider()
        self._pdf_service = PDFService(directorio_salida=config.pdf_output_dir)
        self._agente = AgenteResearch(
            llm_provider=self._llm_provider,
            search_provider=self._search_provider,
            max_busquedas=config.agent_max_searches,
        )

        logger.info(
            "ReportService inicializado: llm=%s, search=%s",
            self._llm_provider.nombre,
            self._search_provider.nombre,
        )

    async def generar_informe(
        self, tema: str
    ) -> tuple[InformeResearch, Path]:
        """
        Genera un informe completo sobre el tema dado.

        Flujo:
        1. El agente busca información y la sintetiza
        2. Se genera el PDF del informe
        3. Se actualiza el informe con la URL del PDF
        4. TODO v2: Persistir en storage

        Args:
            tema: El tema o consulta a investigar

        Returns:
            Tupla (informe, ruta_pdf) con el informe completo y la ruta al PDF

        Raises:
            AgentError: Si el agente no puede completar la investigación
            GeneracionPDFError: Si falla la generación del PDF
        """
        inicio = time.time()
        logger.info("ReportService: iniciando informe para tema='%s'", tema)

        # Paso 1: Ejecutar el agente de investigación
        informe = await self._agente.investigar(tema)

        # Paso 2: Generar el PDF
        ruta_pdf = self._pdf_service.generar(informe)

        # Paso 3: Actualizar el informe con la URL de descarga
        informe.url_pdf = f"/api/pdf/{informe.id}"

        # TODO v2: Persistir el informe en storage
        # await self._storage_provider.guardar_informe(informe)

        duracion = time.time() - inicio
        logger.info(
            "ReportService: informe completado en %.2fs | id=%s",
            duracion,
            informe.id,
        )

        return informe, ruta_pdf

    def verificar_proveedores(self) -> dict[str, bool]:
        """
        Verifica el estado de disponibilidad de todos los proveedores.

        Útil para el endpoint de health check.

        Returns:
            Dict con el estado de cada proveedor
        """
        return {
            "llm": self._llm_provider.esta_disponible(),
            "busqueda": True,  # DuckDuckGo no tiene health check previo
            "pdf": True,       # WeasyPrint no necesita conexión externa
        }
