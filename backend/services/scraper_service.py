"""
Servicio de scraping para obtener el contenido completo de las fuentes.

Usa trafilatura para extraer texto limpio (sin nav/ads/footers) de cada URL.
Se ejecuta después de la búsqueda y antes de la síntesis con LLM, enriqueciendo
el fragmento de cada ResultadoBusqueda con el artículo completo.

Sin API key ni costo adicional — solo httpx + trafilatura.
"""

import asyncio
import logging

import httpx
import trafilatura

from models.report import ResultadoBusqueda

logger = logging.getLogger(__name__)

# Máximo de caracteres a conservar por fuente en el prompt del LLM.
# ~3000 chars ≈ ~750 tokens — buen balance entre contexto y costo/velocidad.
MAX_CHARS_CONTENIDO = 3000

# Timeout por request HTTP (algunos sitios lentos)
TIMEOUT_SEGUNDOS = 10

# Máximo de fuentes a scrapear (las primeras N, ordenadas por relevancia)
MAX_FUENTES_A_SCRAPEAR = 10


async def enriquecer_fuentes(
    fuentes: list[ResultadoBusqueda],
) -> list[ResultadoBusqueda]:
    """
    Descarga y extrae el contenido completo de las primeras N fuentes en paralelo.

    Las fuentes que no se puedan scrapear conservan su fragmento original.
    Nunca falla: los errores por fuente son silenciosos (warning en log).

    Args:
        fuentes: Lista de ResultadoBusqueda con fragmentos cortos de buscador

    Returns:
        La misma lista con .fragmento reemplazado por el contenido completo
        donde el scraping fue exitoso
    """
    a_scrapear = fuentes[:MAX_FUENTES_A_SCRAPEAR]
    resto = fuentes[MAX_FUENTES_A_SCRAPEAR:]

    logger.info(
        "Scraping de %d fuentes (de %d totales)...", len(a_scrapear), len(fuentes)
    )

    async with httpx.AsyncClient(
        timeout=TIMEOUT_SEGUNDOS,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
    ) as cliente:
        tareas = [_scrapear_fuente(cliente, fuente) for fuente in a_scrapear]
        enriquecidas = await asyncio.gather(*tareas)

    exitosos = sum(
        1 for orig, enr in zip(a_scrapear, enriquecidas)
        if enr.fragmento != orig.fragmento
    )
    logger.info("Scraping completado: %d/%d fuentes enriquecidas", exitosos, len(a_scrapear))

    return list(enriquecidas) + resto


async def _scrapear_fuente(
    cliente: httpx.AsyncClient,
    fuente: ResultadoBusqueda,
) -> ResultadoBusqueda:
    """
    Descarga una URL y extrae su contenido principal con trafilatura.

    Si falla (timeout, 4xx, 5xx, o trafilatura no extrae nada), retorna
    la fuente original sin modificar.

    Args:
        cliente: Cliente httpx compartido
        fuente: La fuente a enriquecer

    Returns:
        Fuente con .fragmento actualizado, o la original si falló
    """
    try:
        respuesta = await cliente.get(fuente.url)
        respuesta.raise_for_status()

        # trafilatura es síncrono — lo corremos en thread para no bloquear el loop
        contenido = await asyncio.to_thread(
            trafilatura.extract,
            respuesta.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )

        if not contenido or len(contenido.strip()) < 100:
            logger.debug("trafilatura no extrajo contenido útil de: %s", fuente.url)
            return fuente

        contenido_truncado = contenido[:MAX_CHARS_CONTENIDO]
        logger.debug(
            "Scraping OK: %s → %d chars", fuente.url, len(contenido_truncado)
        )

        # Retornar una copia con el fragmento enriquecido
        return fuente.model_copy(update={"fragmento": contenido_truncado})

    except httpx.TimeoutException:
        logger.debug("Timeout scrapeando: %s", fuente.url)
    except httpx.HTTPStatusError as e:
        logger.debug("HTTP %d scrapeando: %s", e.response.status_code, fuente.url)
    except Exception as e:
        logger.debug("Error scrapeando %s: %s", fuente.url, e)

    return fuente
