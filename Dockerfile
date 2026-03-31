# ═══════════════════════════════════════════════════
# Dockerfile — Backend del Agente de Research
# ═══════════════════════════════════════════════════
# Multi-stage build: instala dependencias del sistema para WeasyPrint
# y luego copia el código de la aplicación.

FROM python:3.11-slim AS base

# Dependencias del sistema necesarias para WeasyPrint (Cairo, Pango, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint: renderizado HTML/CSS a PDF
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Fuentes con soporte completo de caracteres en español
    fonts-dejavu \
    fonts-liberation \
    # Herramientas de red (healthcheck)
    curl \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements primero (cacheo de Docker layers)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY backend/ .

# Crear directorios de datos (serán sobreescritos por volúmenes en producción)
RUN mkdir -p /app/data/pdfs /app/data/chroma /app/data/db

# Usuario no-root por seguridad
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Puerto expuesto
EXPOSE 8000

# Variables de entorno por defecto (sobreescritas por .env en docker-compose)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
