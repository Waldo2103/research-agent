"""
Fixtures compartidos para todos los tests del agente de research.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from models.report import (
    AnalisisSentimiento,
    InformeResearch,
    ResultadoBusqueda,
)


@pytest.fixture
def resultado_busqueda_ejemplo():
    """Un ResultadoBusqueda de ejemplo para usar en tests."""
    return ResultadoBusqueda(
        titulo="Artículo de prueba",
        url="https://ejemplo.com/articulo",
        fragmento="Este es un fragmento de texto de prueba para los tests.",
        fecha_consulta=datetime(2026, 3, 31, 12, 0, 0),
    )


@pytest.fixture
def informe_ejemplo():
    """Un InformeResearch completo de ejemplo para usar en tests."""
    return InformeResearch(
        id="test-id-1234",
        tema="tema de prueba",
        fecha_creacion=datetime(2026, 3, 31, 12, 0, 0),
        resumen_ejecutivo="Este es un resumen ejecutivo de prueba.\n\nSegundo párrafo.",
        puntos_a_favor=["Punto positivo 1", "Punto positivo 2"],
        puntos_en_contra=["Punto negativo 1"],
        analisis_sentimiento=AnalisisSentimiento(
            clasificacion="neutro",
            puntaje=0.1,
            justificacion="Sentimiento balanceado para el test.",
        ),
        conclusiones="Conclusiones de prueba.",
        recomendaciones=["Recomendación 1"],
        fuentes=[
            ResultadoBusqueda(
                titulo="Fuente de prueba",
                url="https://ejemplo.com",
                fragmento="Fragmento de prueba",
                fecha_consulta=datetime(2026, 3, 31, 12, 0, 0),
            )
        ],
    )


@pytest.fixture
def mock_llm_modelo():
    """Mock de un BaseChatModel de LangChain."""
    modelo = MagicMock()
    # Simular respuesta válida de consultas
    respuesta_consultas = MagicMock()
    respuesta_consultas.content = '["consulta 1", "consulta 2", "consulta 3"]'
    modelo.ainvoke = AsyncMock(return_value=respuesta_consultas)
    return modelo
