"""
Agente de investigación principal.

Flujo:
  1. Recibe un tema
  2. Genera consultas de búsqueda via LLM
  3. Ejecuta las búsquedas en paralelo
  4. Sintetiza los resultados en un informe estructurado via LLM
  5. Retorna un InformeResearch validado por Pydantic
"""

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from models.report import AnalisisSentimiento, InformeResearch, ResultadoBusqueda
from providers.llm.base_llm import BaseLLMProvider
from providers.search.base_search import BaseSearchProvider, ProveedorBusquedaError
from services.scraper_service import enriquecer_fuentes

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# EXCEPCIONES DEL AGENTE
# ─────────────────────────────────────────────────────────────────────────────


class AgentError(Exception):
    """Error general del agente de investigación."""
    pass


class ErrorSintesisLLM(AgentError):
    """El LLM no pudo generar una respuesta válida tras los reintentos."""
    pass


class ErrorBusquedas(AgentError):
    """Todas las búsquedas fallaron."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_SISTEMA_CONSULTAS = """Eres un asistente que genera listas de búsqueda web.
Tu única tarea es responder con un array JSON de strings. Nada más.
REGLA ABSOLUTA: respondés SOLO con el JSON. Sin explicaciones, sin texto antes ni después."""

PROMPT_CONSULTAS = """Tema a investigar: "{tema}"

Generá exactamente {num_consultas_max} frases de búsqueda en español sobre ese tema.
Cubrí estos ángulos (uno por frase):
1. Información general y trayectoria
2. Noticias recientes
3. Vida personal o historia
4. Logros y gestión
5. Críticas y controversias
6. Vínculos políticos o institucionales
7. Opiniones de terceros
8. Datos y estadísticas

REGLAS IMPORTANTES:
- Cada frase debe ser texto simple, como se escribe en Google
- NO uses comillas dentro de las frases
- NO uses operadores como site:, filetype:, intitle:, guiones ni paréntesis
- Las frases deben ser cortas (máximo 8 palabras)

Respondé ÚNICAMENTE con este formato JSON, sin ningún otro texto:
["frase 1", "frase 2", "frase 3", "frase 4", "frase 5", "frase 6", "frase 7", "frase 8"]"""


PROMPT_SISTEMA_INFORME = """Eres un analista de investigación senior con experiencia en \
inteligencia política, periodismo de datos y análisis estratégico. Tu tarea es analizar \
resultados de búsqueda web y producir informes ejecutivos exhaustivos y detallados en español.
Siempre respondés ÚNICAMENTE con JSON válido, sin texto adicional ni explicaciones.
Respondé siempre en español. Sé exhaustivo y detallado. No uses respuestas cortas \
ni superficiales. El usuario necesita información profunda y completa."""

PROMPT_INFORME = """Analizá los siguientes resultados de búsqueda sobre el tema "{tema}" \
y generá un informe ejecutivo exhaustivo y detallado en español.

RESULTADOS DE BÚSQUEDA:
{resultados}

Generá un informe con EXACTAMENTE este formato JSON (no agregués campos extra):
{{
  "resumen_ejecutivo": "MÍNIMO 5 párrafos separados por \\n\\n. Debe incluir: (1) quién es o qué es el tema investigado con contexto completo, (2) contexto histórico y antecedentes relevantes, (3) principales logros, propuestas o aspectos positivos encontrados, (4) principales críticas, problemas o aspectos negativos encontrados, (5) situación actual y perspectivas. Cada párrafo debe tener al menos 4 oraciones.",
  "puntos_a_favor": [
    "Punto 1 con título claro: explicación detallada en una o dos oraciones que justifique y desarrolle este punto con información concreta de las fuentes.",
    "Punto 2 con título claro: explicación detallada...",
    "Punto 3 con título claro: explicación detallada...",
    "Punto 4 con título claro: explicación detallada...",
    "Punto 5 con título claro: explicación detallada...",
    "Punto 6 con título claro: explicación detallada..."
  ],
  "puntos_en_contra": [
    "Punto 1 con título claro: explicación detallada en una o dos oraciones que justifique y desarrolle este punto con información concreta de las fuentes.",
    "Punto 2 con título claro: explicación detallada...",
    "Punto 3 con título claro: explicación detallada...",
    "Punto 4 con título claro: explicación detallada..."
  ],
  "analisis_sentimiento": {{
    "clasificacion": "positivo",
    "puntaje": 0.4,
    "justificacion": "Párrafo de MÍNIMO 150 palabras explicando el tono general encontrado en las fuentes consultadas. Debe incluir: el tipo de cobertura mediática predominante (positiva/negativa/neutral), ejemplos concretos del tono usado en las fuentes, análisis de si el sentimiento varía según el tipo de fuente (medios oficiales vs. independientes, redes sociales vs. prensa), y una evaluación de la credibilidad y consistencia de las fuentes encontradas."
  }},
  "conclusiones": "MÍNIMO 3 párrafos separados por \\n\\n con análisis profundo. Primer párrafo: síntesis de los hallazgos más importantes. Segundo párrafo: evaluación crítica equilibrada considerando el contexto. Tercer párrafo: perspectivas futuras y factores clave a monitorear.",
  "recomendaciones": [
    "Recomendación 1 concreta y accionable: descripción específica de qué hacer, cuándo y por qué.",
    "Recomendación 2 concreta y accionable: descripción específica...",
    "Recomendación 3 concreta y accionable: descripción específica...",
    "Recomendación 4 concreta y accionable: descripción específica...",
    "Recomendación 5 concreta y accionable: descripción específica..."
  ],
  "informe_detallado": "Artículo periodístico de MÍNIMO 8 párrafos separados por \\n\\n. Redactado como nota de investigación en profundidad. Estructura sugerida: (1) presentación del sujeto con datos concretos, (2) origen e historia personal/institucional, (3) llegada al cargo y contexto, (4) gestión y decisiones clave detalladas, (5) logros con datos y fechas, (6) controversias, críticas y causas con detalle, (7) vínculos políticos, económicos e institucionales, (8) situación actual y perspectivas. Cada párrafo mínimo 5 oraciones. Diferenciá hechos de opiniones. Usá citas [N] cuando corresponda."
}}

REGLAS ESTRICTAS:
- Si los resultados incluyen información sobre múltiples personas u entidades con nombres \
similares, identificá cuál corresponde al tema solicitado y usá ÚNICAMENTE esa información. \
Ignorá completamente los resultados sobre otros homónimos o personas distintas.
- clasificacion debe ser exactamente "positivo", "negativo" o "neutro"
- puntaje debe ser un número entre -1.0 (muy negativo) y 1.0 (muy positivo)
- Cada punto_a_favor y punto_en_contra DEBE incluir una explicación, no solo un título
- La justificacion del sentimiento DEBE tener al menos 150 palabras
- Si no hay suficiente información sobre algún aspecto, indicarlo explícitamente
- El análisis debe ser objetivo y basado en los resultados encontrados
- No inventar información que no esté en las fuentes
- CITAS OBLIGATORIAS: cuando una afirmación proviene de una fuente específica, incluí \
la referencia entre corchetes al final de la oración. Ejemplo: "X logró Y en 2023. [3]" \
o "Según fuentes oficiales, Z ocurrió el año pasado. [1][5]". Los números corresponden \
al número de fuente en la lista de RESULTADOS DE BÚSQUEDA (Fuente 1, Fuente 2, etc.). \
Usá citas en el resumen_ejecutivo, puntos_a_favor, puntos_en_contra, analisis_sentimiento \
y conclusiones.
- RESPONDER ÚNICAMENTE CON EL JSON VÁLIDO, sin texto antes ni después"""


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────


class AgenteResearch:
    """
    Agente de investigación que orquesta búsquedas web y síntesis con LLM.

    Implementa un pipeline en dos fases:
    1. Generación de consultas → búsquedas paralelas
    2. Síntesis de resultados → informe estructurado

    Este enfoque es más predecible que un ReAct loop completo
    con modelos locales (Ollama), donde el seguimiento de instrucciones
    puede ser inconsistente.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        search_provider: BaseSearchProvider,
        max_busquedas: int = 5,
        max_reintentos: int = 2,
    ) -> None:
        """
        Inicializa el agente de investigación.

        Args:
            llm_provider: Proveedor de LLM para generación y síntesis
            search_provider: Proveedor de búsqueda web
            max_busquedas: Número máximo de búsquedas a ejecutar
            max_reintentos: Reintentos si el LLM devuelve JSON inválido
        """
        self._llm_provider = llm_provider
        self._search_provider = search_provider
        self._max_busquedas = max_busquedas
        self._max_reintentos = max_reintentos

        logger.info(
            "AgenteResearch inicializado: llm=%s, search=%s, max_busquedas=%d",
            llm_provider.nombre,
            search_provider.nombre,
            max_busquedas,
        )

    async def investigar(
        self,
        tema: str,
        on_progreso: Optional[Callable[[int, int, str], Awaitable[None]]] = None,
    ) -> InformeResearch:
        """
        Ejecuta el flujo completo de investigación sobre un tema.

        Args:
            tema: El tema o consulta a investigar

        Returns:
            InformeResearch con todas las secciones completadas

        Raises:
            AgentError: Si el agente no puede completar la investigación
        """
        inicio = time.time()
        informe_id = str(uuid.uuid4())

        logger.info("=== INICIANDO INVESTIGACIÓN ===")
        logger.info("ID: %s | Tema: %s", informe_id, tema)

        async def _emit(paso: int, total: int, mensaje: str) -> None:
            logger.info("Paso %d/%d: %s", paso, total, mensaje)
            if on_progreso:
                await on_progreso(paso, total, mensaje)

        # Paso 1: Generar consultas de búsqueda
        await _emit(1, 5, "Generando consultas de búsqueda...")
        consultas = await self._generar_consultas(tema)
        logger.info("Consultas generadas (%d): %s", len(consultas), consultas)

        # Paso 2: Ejecutar búsquedas en paralelo
        await _emit(2, 5, f"Ejecutando {len(consultas)} búsquedas en paralelo...")
        resultados = await self._buscar_en_paralelo(consultas)
        logger.info("Total de resultados obtenidos: %d", len(resultados))

        if not resultados:
            raise ErrorBusquedas(
                f"No se encontraron resultados para el tema: '{tema}'"
            )

        # Paso 3: Enriquecer fuentes con contenido completo via scraping
        await _emit(3, 5, f"Descargando contenido completo de {min(len(resultados), 10)} fuentes...")
        resultados = await enriquecer_fuentes(resultados)

        # Paso 4: Sintetizar informe
        await _emit(4, 5, "Sintetizando informe con IA...")
        informe = await self._sintetizar_informe(
            tema=tema,
            resultados=resultados,
            informe_id=informe_id,
        )

        duracion = time.time() - inicio
        logger.info(
            "=== INVESTIGACIÓN COMPLETADA === ID: %s | Duración: %.2fs",
            informe_id,
            duracion,
        )

        return informe

    async def _generar_consultas(self, tema: str) -> list[str]:
        """
        Usa el LLM para generar consultas de búsqueda diversas sobre el tema.

        Genera entre 5 y max_busquedas consultas cubriendo múltiples ángulos:
        vida personal, gestión/logros, controversias, vínculos y opiniones.

        Args:
            tema: El tema a investigar

        Returns:
            Lista de consultas de búsqueda en español
        """
        llm = self._llm_provider.get_modelo()
        prompt = PROMPT_CONSULTAS.format(
            tema=tema,
            num_consultas_min=5,
            num_consultas_max=self._max_busquedas,
        )

        for intento in range(self._max_reintentos + 1):
            try:
                respuesta = await llm.ainvoke([
                    SystemMessage(content=PROMPT_SISTEMA_CONSULTAS),
                    HumanMessage(content=prompt),
                ])
                contenido = respuesta.content
                consultas = _extraer_json(contenido)

                if not isinstance(consultas, list):
                    raise ValueError("La respuesta no es un array JSON")

                # Filtrar y limpiar las consultas
                consultas_limpias = [
                    str(c).strip() for c in consultas if str(c).strip()
                ]

                if not consultas_limpias:
                    raise ValueError("Array de consultas vacío")

                return consultas_limpias[: self._max_busquedas]

            except (ValueError, json.JSONDecodeError) as e:
                logger.warning(
                    "Intento %d/%d fallido al parsear consultas: %s",
                    intento + 1,
                    self._max_reintentos + 1,
                    e,
                )
                if intento == self._max_reintentos:
                    # Fallback: construir queries cortas desde las primeras
                    # palabras del tema (evitar enviar 300 chars a DuckDuckGo)
                    tema_corto = " ".join(tema.split()[:6])
                    logger.warning(
                        "Usando fallback de consultas cortas: '%s'", tema_corto
                    )
                    return [
                        tema_corto,
                        f"{tema_corto} noticias",
                        f"{tema_corto} controversias",
                        f"{tema_corto} gestión",
                    ]

        return [tema]

    async def _buscar_en_paralelo(
        self, consultas: list[str]
    ) -> list[ResultadoBusqueda]:
        """
        Ejecuta las búsquedas con concurrencia controlada para evitar rate limiting.

        DuckDuckGo bloquea temporalmente IPs que hacen muchas peticiones simultáneas.
        El semáforo limita a 2 búsquedas en paralelo: reduce el tiempo total respecto
        a ejecución secuencial, sin saturar el proveedor de búsqueda.

        Args:
            consultas: Lista de consultas de búsqueda

        Returns:
            Lista de resultados deduplicados por URL
        """
        # Máximo 2 búsquedas simultáneas para no disparar rate limiting de DuckDuckGo
        semaforo = asyncio.Semaphore(2)

        async def buscar_con_semaforo(consulta: str) -> list[ResultadoBusqueda]:
            async with semaforo:
                return await self._buscar_con_fallback(consulta)

        tareas = [buscar_con_semaforo(consulta) for consulta in consultas]
        resultados_por_consulta = await asyncio.gather(*tareas)

        # Aplanar y deduplicar por URL
        urls_vistas: set[str] = set()
        resultados_unicos: list[ResultadoBusqueda] = []

        for resultados in resultados_por_consulta:
            for resultado in resultados:
                if resultado.url not in urls_vistas:
                    urls_vistas.add(resultado.url)
                    resultados_unicos.append(resultado)

        logger.info(
            "Resultados únicos tras deduplicación: %d", len(resultados_unicos)
        )
        return resultados_unicos

    async def _buscar_con_fallback(
        self, consulta: str
    ) -> list[ResultadoBusqueda]:
        """
        Ejecuta una búsqueda individual con manejo de errores.

        Si la búsqueda falla, retorna una lista vacía en lugar de
        propagar el error (para no cancelar las demás búsquedas paralelas).

        Args:
            consulta: La consulta de búsqueda

        Returns:
            Lista de resultados, vacía si la búsqueda falla
        """
        try:
            return await self._search_provider.buscar(consulta)
        except ProveedorBusquedaError as e:
            logger.warning("Búsqueda fallida para '%s': %s", consulta, e)
            return []

    async def _sintetizar_informe(
        self,
        tema: str,
        resultados: list[ResultadoBusqueda],
        informe_id: str,
    ) -> InformeResearch:
        """
        Usa el LLM para sintetizar los resultados en un informe estructurado.

        Args:
            tema: El tema investigado
            resultados: Resultados de las búsquedas
            informe_id: ID único para el informe

        Returns:
            InformeResearch completamente poblado

        Raises:
            ErrorSintesisLLM: Si el LLM no genera JSON válido tras todos los reintentos
        """
        llm = self._llm_provider.get_modelo()

        # Formatear resultados para el prompt (limitar para no exceder el contexto)
        # Con scraping habilitado cada fuente trae hasta 800 chars (vs 300 sin scraping).
        # 8 fuentes × 800 chars cabe holgadamente en el tier gratuito de Groq (12k TPM).
        resultados_texto = _formatear_resultados_para_prompt(resultados, max_items=8)

        prompt = PROMPT_INFORME.format(
            tema=tema,
            resultados=resultados_texto,
        )

        for intento in range(self._max_reintentos + 1):
            try:
                logger.debug(
                    "Llamada al LLM para síntesis, intento %d/%d",
                    intento + 1,
                    self._max_reintentos + 1,
                )
                respuesta = await llm.ainvoke([
                    SystemMessage(content=PROMPT_SISTEMA_INFORME),
                    HumanMessage(content=prompt),
                ])
                datos = _extraer_json(respuesta.content)

                return _construir_informe(
                    datos=datos,
                    tema=tema,
                    fuentes=resultados,
                    informe_id=informe_id,
                )

            except (ValueError, json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    "Intento %d/%d fallido al parsear informe: %s",
                    intento + 1,
                    self._max_reintentos + 1,
                    e,
                )
                if intento == self._max_reintentos:
                    raise ErrorSintesisLLM(
                        f"El LLM no pudo generar un informe válido tras "
                        f"{self._max_reintentos + 1} intentos. Último error: {e}"
                    ) from e

        # Este punto nunca se alcanza, pero satisface el type checker
        raise ErrorSintesisLLM("Fallo inesperado en la síntesis")


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────


def _extraer_json(texto: str) -> dict | list:
    """
    Extrae JSON de una respuesta de LLM que puede incluir texto adicional.

    Intenta múltiples estrategias de extracción para ser robusto
    con modelos que a veces incluyen texto antes/después del JSON.

    Args:
        texto: El texto completo de la respuesta del LLM

    Returns:
        El objeto JSON parseado (dict o list)

    Raises:
        json.JSONDecodeError: Si no se pudo extraer JSON válido
        ValueError: Si el texto no contiene JSON reconocible
    """
    texto = texto.strip()

    # Estrategia 1: el texto completo es JSON válido
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # Estrategia 2: JSON dentro de bloques de código markdown
    patron_codigo = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    match = re.search(patron_codigo, texto)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Estrategia 3: el primer objeto JSON `{...}` en el texto
    patron_objeto = r"\{[\s\S]*\}"
    match = re.search(patron_objeto, texto)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Estrategia 4: el primer array JSON `[...]` en el texto
    patron_array = r"\[[\s\S]*\]"
    match = re.search(patron_array, texto)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Estrategia 5: extracción línea por línea para arrays con comillas internas.
    # llama3 a veces genera strings tipo `"("término") - descripción"` donde las
    # comillas internas rompen el JSON. Tomamos todo entre la PRIMERA y ÚLTIMA
    # comilla de cada línea, lo que recupera el contenido útil.
    items_recuperados = []
    for linea in texto.split("\n"):
        linea = linea.strip().rstrip(",").strip("[]").strip()
        if '"' not in linea:
            continue
        primera = linea.find('"')
        ultima = linea.rfind('"')
        if primera == ultima:
            continue  # Solo una comilla — línea no parseable
        contenido = linea[primera + 1 : ultima].strip()
        if len(contenido) >= 4:  # Ignorar strings trivialmente cortos
            items_recuperados.append(contenido)

    if len(items_recuperados) >= 2:
        logger.debug(
            "Estrategia 5 recuperó %d items del array con comillas internas",
            len(items_recuperados),
        )
        return items_recuperados

    raise ValueError(
        f"No se pudo extraer JSON válido de la respuesta del LLM. "
        f"Primeros 300 caracteres: {texto[:300]}"
    )


def _formatear_resultados_para_prompt(
    resultados: list[ResultadoBusqueda], max_items: int = 8
) -> str:
    """
    Formatea los resultados de búsqueda como texto para incluir en el prompt.

    Limita tanto la cantidad de resultados como la longitud de cada fragmento
    para mantener el prompt dentro de un tamaño manejable para Ollama en CPU.
    Con llama3 8B en CPU, cada ~1000 tokens adicionales suma ~15-20s de inferencia.

    Args:
        resultados: Lista de resultados de búsqueda
        max_items: Número máximo de resultados a incluir

    Returns:
        Texto formateado con los resultados
    """
    # 1200 chars por fuente ≈ 300 tokens → 8 fuentes ≈ 2400 tokens de contenido
    # Groq free tier: 12k TPM. Prompt (~2000) + contenido (~2400) + output (~5000) ≈ 9400 < 12k
    MAX_CHARS_FRAGMENTO = 1200

    lineas = []
    for i, r in enumerate(resultados[:max_items], 1):
        fragmento = r.fragmento
        if len(fragmento) > MAX_CHARS_FRAGMENTO:
            fragmento = fragmento[:MAX_CHARS_FRAGMENTO] + "..."
        lineas.append(f"--- Fuente {i} ---")
        lineas.append(f"Título: {r.titulo}")
        lineas.append(f"URL: {r.url}")
        lineas.append(f"Contenido: {fragmento}")
        lineas.append("")
    return "\n".join(lineas)


def _construir_informe(
    datos: dict,
    tema: str,
    fuentes: list[ResultadoBusqueda],
    informe_id: str,
) -> InformeResearch:
    """
    Construye un InformeResearch validado desde el dict retornado por el LLM.

    Args:
        datos: Dict con los datos del informe parseados del JSON del LLM
        tema: El tema investigado
        fuentes: Lista completa de resultados de búsqueda (para las citas)
        informe_id: ID único del informe

    Returns:
        InformeResearch validado por Pydantic

    Raises:
        KeyError: Si faltan campos requeridos en el dict
        ValueError: Si los valores no pasan la validación de Pydantic
    """
    sentimiento_raw = datos.get("analisis_sentimiento", {})

    # Normalizar la clasificación del sentimiento
    clasificacion = str(
        sentimiento_raw.get("clasificacion", "neutro")
    ).lower().strip()
    if clasificacion not in ("positivo", "negativo", "neutro"):
        logger.warning(
            "Clasificación de sentimiento inválida '%s', usando 'neutro'", clasificacion
        )
        clasificacion = "neutro"

    # Normalizar el puntaje del sentimiento
    try:
        puntaje = float(sentimiento_raw.get("puntaje", 0.0))
        puntaje = max(-1.0, min(1.0, puntaje))  # Clamping al rango válido
    except (TypeError, ValueError):
        puntaje = 0.0

    sentimiento = AnalisisSentimiento(
        clasificacion=clasificacion,
        puntaje=puntaje,
        justificacion=str(sentimiento_raw.get("justificacion", "")),
    )

    return InformeResearch(
        id=informe_id,
        tema=tema,
        fecha_creacion=datetime.now(),
        resumen_ejecutivo=str(datos.get("resumen_ejecutivo", "")),
        puntos_a_favor=_asegurar_lista(datos.get("puntos_a_favor", [])),
        puntos_en_contra=_asegurar_lista(datos.get("puntos_en_contra", [])),
        analisis_sentimiento=sentimiento,
        conclusiones=str(datos.get("conclusiones", "")),
        recomendaciones=_asegurar_lista(datos.get("recomendaciones", [])),
        informe_detallado=str(datos.get("informe_detallado", "")),
        fuentes=fuentes,
    )


def _asegurar_lista(valor) -> list[str]:
    """
    Convierte un valor a una lista de strings de forma segura.

    Args:
        valor: Puede ser lista, string u otro tipo

    Returns:
        Lista de strings limpia
    """
    if isinstance(valor, list):
        return [str(item).strip() for item in valor if str(item).strip()]
    if isinstance(valor, str) and valor.strip():
        return [valor.strip()]
    return []
