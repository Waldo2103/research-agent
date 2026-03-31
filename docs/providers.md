# Guía de Proveedores

## Tabla de Proveedores

| Categoría     | Proveedor Activo (v1) | Alternativas Disponibles     | Variable de entorno  |
|---------------|----------------------|------------------------------|----------------------|
| LLM           | Ollama (llama3)      | Groq ✅, OpenAI, Anthropic   | `LLM_PROVIDER`       |
| Búsqueda web  | DuckDuckGo           | Tavily, SerpAPI, Brave Search| `SEARCH_PROVIDER`    |
| Vector Store  | ChromaDB (local)     | Pinecone, Weaviate           | `VECTOR_PROVIDER`    |
| Storage       | SQLite (TODO v2)     | PostgreSQL                   | `STORAGE_PROVIDER`   |
| PDF Generator | WeasyPrint           | ReportLab, FPDF2             | `PDF_PROVIDER`       |

---

## 1. Proveedor LLM

### Ollama (por defecto — gratis, local)

**Cuándo usarlo:** siempre que no haya presupuesto para APIs de pago, o cuando la privacidad de los datos sea crítica (los datos del club no salen del servidor).

**Requisitos:**
- Ollama instalado en el host (`https://ollama.ai/download`) o en Docker
- Modelo descargado: `ollama pull llama3`

**Variables de entorno:**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434   # URL del servicio en docker-compose
OLLAMA_MODEL=llama3                   # O llama3:70b para mayor calidad
OLLAMA_TEMPERATURE=0.3               # 0.0 = determinístico, 1.0 = creativo
OLLAMA_MAX_TOKENS=4096
```

**Modelos recomendados para español:**
| Modelo         | RAM necesaria | Calidad español | Velocidad |
|----------------|---------------|-----------------|-----------|
| llama3 (8B)    | 8 GB          | Buena           | Rápido    |
| llama3:70b     | 48 GB         | Muy buena       | Lento     |
| mistral (7B)   | 8 GB          | Muy buena       | Rápido    |
| mixtral:8x7b   | 48 GB         | Excelente       | Medio     |

---

### OpenAI (TODO — requiere API key de pago)

**Cuándo usarlo:** cuando se necesite mayor calidad de síntesis o velocidad superior a Ollama.

**Pasos para habilitar:**
1. Obtener API key en `https://platform.openai.com/api-keys`
2. Editar `.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o           # O gpt-4o-mini para menor costo
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=4096
```
3. Reiniciar el servicio: `docker-compose restart backend`

**No se requiere tocar código.** El factory en `config.py` instancia `OpenAIProvider` automáticamente.

---

### Anthropic Claude (TODO — requiere API key de pago)

**Cuándo usarlo:** cuando se quiera la mejor calidad de síntesis en español y análisis de texto largo.

**Pasos para habilitar:**
1. Obtener API key en `https://console.anthropic.com/`
2. Editar `.env`:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514    # O claude-opus-4-6 para mayor calidad
ANTHROPIC_MAX_TOKENS=4096
```
3. Reiniciar: `docker-compose restart backend`

---

### Groq (implementado — tier gratuito disponible)

**Cuándo usarlo:** alternativa recomendada a Ollama cuando se quiere mayor calidad sin costo. Groq usa hardware especializado (LPU) que ejecuta llama-3.3-70b gratis, con velocidad 5-10x superior a Ollama en CPU y calidad muy superior a llama3 8B local.

**Ventajas sobre Ollama local:**
- Sin GPU ni hardware potente requerido en el servidor
- `llama-3.3-70b-versatile` es gratis y de alta calidad
- Respuestas más largas (hasta 128k tokens de contexto)
- Velocidad: ~1-2s de latencia vs. ~2-3 minutos de Ollama en CPU

**Pasos para habilitar:**
1. Crear cuenta gratuita en `https://console.groq.com/`
2. Ir a **Settings → API Keys → Create API Key**
3. Editar `.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...                   # Pegar la key generada
GROQ_MODEL=llama-3.3-70b-versatile    # Recomendado
GROQ_TEMPERATURE=0.3
GROQ_MAX_TOKENS=8192
```
4. Reiniciar: `docker-compose restart backend`

**Modelos disponibles:**
| Modelo | Contexto | Calidad | Velocidad |
|---|---|---|---|
| llama-3.3-70b-versatile | 128k | Excelente | Rápido |
| llama3-8b-8192 | 8k | Buena | Muy rápido |
| mixtral-8x7b-32768 | 32k | Muy buena | Rápido |

---

## 2. Proveedor de Búsqueda Web

### DuckDuckGo (por defecto — gratis, sin API key)

**Cuándo usarlo:** siempre en la versión base. Sin límites estrictos de rate, sin costo.

**Variables de entorno:**
```env
SEARCH_PROVIDER=duckduckgo
SEARCH_MAX_RESULTS=10          # Resultados por búsqueda
SEARCH_REGION=ar-es            # ar-es para Argentina, es-es para España
SEARCH_SAFESEARCH=off          # off | moderate | strict
```

**Limitación conocida:** DuckDuckGo no tiene una API oficial. La librería `duckduckgo-search` hace scraping. Puede ser bloqueada temporalmente si hay demasiadas consultas en poco tiempo. Solución: aumentar `SEARCH_DELAY_SECONDS`.

---

### Tavily (TODO — tier gratuito: 1000 búsquedas/mes)

**Cuándo usarlo:** cuando se necesiten resultados más frescos o búsqueda de noticias recientes.

**Pasos para habilitar:**
1. Registrarse en `https://tavily.com/` (plan gratuito disponible)
2. Editar `.env`:
```env
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-...
SEARCH_MAX_RESULTS=10
TAVILY_SEARCH_DEPTH=advanced   # basic | advanced
TAVILY_INCLUDE_DOMAINS=        # Dejar vacío para buscar en todo
TAVILY_EXCLUDE_DOMAINS=        # Dominios a excluir (separados por coma)
```
3. Reiniciar: `docker-compose restart backend`

---

### SerpAPI (TODO — requiere plan de pago)

**Cuándo usarlo:** cuando se necesite búsqueda en Google (resultados más relevantes para Argentina).

**Pasos para habilitar:**
1. Obtener API key en `https://serpapi.com/`
2. Editar `.env`:
```env
SEARCH_PROVIDER=serpapi
SERPAPI_API_KEY=...
SERPAPI_ENGINE=google
SERPAPI_GL=ar                  # País: ar para Argentina
SERPAPI_HL=es                  # Idioma: es para español
SEARCH_MAX_RESULTS=10
```

---

### Brave Search (TODO — API gratuita: 2000 búsquedas/mes)

**Cuándo usarlo:** alternativa gratuita a DuckDuckGo con API oficial y mayor control.

**Pasos para habilitar:**
1. Obtener API key en `https://brave.com/search/api/`
2. Editar `.env`:
```env
SEARCH_PROVIDER=brave
BRAVE_API_KEY=BSA...
SEARCH_MAX_RESULTS=10
BRAVE_COUNTRY=AR               # País para resultados locales
```

---

## 3. Vector Store

### ChromaDB (por defecto — gratis, local)

**Cuándo usarlo:** siempre en la versión base. Los datos se persisten en disco dentro del contenedor Docker.

**Variables de entorno:**
```env
VECTOR_PROVIDER=chroma
CHROMA_PERSIST_DIR=/app/data/chroma    # Directorio de persistencia
CHROMA_COLLECTION_NAME=research_agent
```

**Dónde se guardan los datos:**
El directorio está montado como volumen Docker en `docker-compose.yml`:
```yaml
volumes:
  - ./data/chroma:/app/data/chroma
```

---

### Pinecone (TODO — tier gratuito disponible)

**Cuándo usarlo:** cuando se necesite escalar a múltiples servidores o tener el vector store en la nube.

**Pasos para habilitar:**
1. Crear cuenta en `https://www.pinecone.io/`
2. Crear un índice con dimensión `4096` (para llama3) o `1536` (para OpenAI embeddings)
3. Editar `.env`:
```env
VECTOR_PROVIDER=pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=research-agent
PINECONE_ENVIRONMENT=us-east-1-aws
```

---

## 4. Storage / Historial de Informes (TODO v2)

### SQLite (TODO v2 — gratis, local)

**Cuándo usarlo:** versión por defecto para v2. Sin servidor adicional.

**Variables de entorno:**
```env
STORAGE_PROVIDER=sqlite
DATABASE_URL=sqlite:///./data/research_agent.db
```

---

### PostgreSQL (TODO v2 — para producción)

**Cuándo usarlo:** cuando el equipo crezca o se necesite acceso concurrente desde múltiples instancias.

**Pasos para habilitar (v2):**
1. Provisionar base de datos (local, Railway, Supabase, etc.)
2. Editar `.env`:
```env
STORAGE_PROVIDER=postgres
DATABASE_URL=postgresql://usuario:contraseña@host:5432/research_agent
```
3. Ejecutar migraciones: `docker-compose exec backend alembic upgrade head`

---

## 5. Generador de PDF

### WeasyPrint (por defecto — gratis, open source)

**No requiere cambios de configuración.** El template HTML/CSS se encuentra en `backend/services/pdf_service.py`.

**Variables de entorno:**
```env
PDF_PROVIDER=weasyprint
PDF_OUTPUT_DIR=/app/data/pdfs     # Directorio de almacenamiento temporal
PDF_FONT=DejaVu Sans              # Fuente con soporte completo de español
```

---

## Cómo Agregar un Nuevo Proveedor

Si necesitás integrar un proveedor que no está en la lista:

### Paso 1: Crear la clase del proveedor

```python
# backend/providers/llm/mi_proveedor.py
from providers.llm.base_llm import BaseLLMProvider

class MiProveedorLLM(BaseLLMProvider):
    """Descripción del proveedor."""

    def __init__(self, api_key: str, modelo: str) -> None:
        self.api_key = api_key
        self.modelo = modelo

    def generar(self, prompt: str) -> str:
        # Implementar llamada a la API
        ...

    def esta_disponible(self) -> bool:
        # Verificar que la API key es válida
        ...
```

### Paso 2: Registrarlo en config.py

```python
# backend/config.py
elif proveedor == "mi_proveedor":
    from providers.llm.mi_proveedor import MiProveedorLLM
    return MiProveedorLLM(
        api_key=os.getenv("MI_PROVEEDOR_API_KEY"),
        modelo=os.getenv("MI_PROVEEDOR_MODEL", "modelo-default")
    )
```

### Paso 3: Agregar variables a .env.example

```env
# Mi Proveedor LLM
MI_PROVEEDOR_API_KEY=     # API key obtenida en https://...
MI_PROVEEDOR_MODEL=modelo-default
```

### Paso 4: Escribir tests

```python
# tests/providers/test_mi_proveedor.py
def test_mi_proveedor_genera_texto():
    proveedor = MiProveedorLLM(api_key="test", modelo="test-model")
    # ... assertions
```

Eso es todo. El agente y los servicios no requieren ningún cambio.
