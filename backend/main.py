"""
Punto de entrada de la API REST.

Define los endpoints de FastAPI y configura la aplicación.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from agent.research_agent import AgentError
from config import (
    asegurar_directorios,
    configurar_logging,
    get_llm_provider,
    obtener_config,
)
from models.report import InformeResearch, RespuestaResearch, SolicitudResearch
from services.pdf_service import GeneracionPDFError
from services.report_service import ReportService

# Configurar logging antes de cualquier otra cosa
configurar_logging()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP / SHUTDOWN
# ─────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Acciones al iniciar y detener la aplicación."""
    # Startup
    logger.info("=== INICIANDO AGENTE DE RESEARCH ===")
    asegurar_directorios()

    config = obtener_config()
    logger.info("Entorno: %s | LLM: %s", config.app_env, config.llm_provider)

    # Verificar que el LLM esté disponible
    llm_provider = get_llm_provider()
    if not llm_provider.esta_disponible():
        logger.warning(
            "Proveedor LLM '%s' no disponible al iniciar. "
            "Verificar configuración en .env",
            llm_provider.nombre,
        )
    else:
        logger.info("Proveedor LLM disponible: %s", llm_provider.nombre)

    yield

    # Shutdown
    logger.info("=== DETENIENDO AGENTE DE RESEARCH ===")


# ─────────────────────────────────────────────────────────────────────────────
# APLICACIÓN FASTAPI
# ─────────────────────────────────────────────────────────────────────────────

config = obtener_config()

app = FastAPI(
    title="Agente de Research",
    description=(
        "API para generación automática de informes de investigación. "
        "Busca información en la web, la analiza con un LLM y genera un PDF."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configurar CORS para que el frontend pueda llamar a la API
origenes_permitidos = [o.strip() for o in config.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Instancia del servicio (se crea una vez al iniciar)
report_service = ReportService()


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/health", tags=["Sistema"])
async def health_check() -> dict:
    """
    Verifica el estado del sistema y sus proveedores.

    Útil para monitoreo y para verificar que el servicio está listo.
    """
    estado_proveedores = report_service.verificar_proveedores()
    todo_ok = all(estado_proveedores.values())

    return {
        "estado": "ok" if todo_ok else "degradado",
        "proveedores": estado_proveedores,
        "llm_provider": config.llm_provider,
        "search_provider": config.search_provider,
    }


@app.post(
    "/api/research",
    response_model=RespuestaResearch,
    tags=["Investigación"],
    summary="Generar un informe de investigación",
)
async def generar_informe(solicitud: SolicitudResearch) -> RespuestaResearch:
    """
    Genera un informe de investigación completo sobre el tema dado.

    El proceso completo incluye:
    1. Generación de consultas de búsqueda
    2. Búsquedas web en paralelo
    3. Síntesis con LLM en español
    4. Generación del PDF

    El informe incluye la URL de descarga del PDF en el campo `url_pdf`.
    """
    import time
    inicio = time.time()

    logger.info("POST /api/research | tema='%s'", solicitud.tema)

    try:
        informe, _ = await report_service.generar_informe(solicitud.tema)
        duracion = time.time() - inicio

        return RespuestaResearch(
            informe=informe,
            duracion_segundos=round(duracion, 2),
        )

    except AgentError as e:
        logger.error("Error del agente para tema='%s': %s", solicitud.tema, e)
        raise HTTPException(
            status_code=500,
            detail=f"El agente no pudo completar la investigación: {e}",
        ) from e

    except GeneracionPDFError as e:
        logger.error("Error al generar PDF para informe %s: %s", e.informe_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"El informe se generó pero falló la creación del PDF: {e}",
        ) from e


@app.get(
    "/api/pdf/{informe_id}",
    tags=["Investigación"],
    summary="Descargar el PDF de un informe",
)
async def descargar_pdf(informe_id: str) -> FileResponse:
    """
    Descarga el PDF de un informe previamente generado.

    Args:
        informe_id: El UUID del informe (provisto en el campo `id` del informe)

    Returns:
        El archivo PDF para descarga
    """
    # Validación básica del ID para prevenir path traversal
    if not informe_id.replace("-", "").isalnum() or len(informe_id) > 36:
        raise HTTPException(status_code=400, detail="ID de informe inválido")

    ruta_pdf = Path(config.pdf_output_dir) / f"{informe_id}.pdf"

    if not ruta_pdf.exists():
        logger.warning("PDF no encontrado: %s", informe_id)
        raise HTTPException(
            status_code=404,
            detail=f"PDF no encontrado para el informe: {informe_id}",
        )

    nombre_descarga = f"informe-{informe_id[:8]}.pdf"
    logger.info("Descargando PDF: %s", informe_id)

    return FileResponse(
        path=str(ruta_pdf),
        media_type="application/pdf",
        filename=nombre_descarga,
    )
