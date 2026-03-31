# Guía de Deployment

## Requisitos Previos

### Para correr local (con Docker — recomendado)
- Docker Desktop 24+ o Docker Engine 24+
- docker-compose v2+
- 8 GB RAM mínimo (16 GB recomendado para llama3:70b)
- 10 GB espacio en disco (para la imagen de Ollama + modelo llama3)

### Para correr local (sin Docker — desarrollo)
- Python 3.11+
- Ollama instalado: `https://ollama.ai/download`
- Dependencias del sistema para WeasyPrint (ver abajo)

---

## Opción A: Correr con Docker (recomendado)

Este es el método estándar para el equipo y para el server casero.

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd research-agent
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con los valores correspondientes. Para la versión base con Ollama y DuckDuckGo, los valores por defecto del `.env.example` son suficientes — no hay que cambiar nada.

### 3. Levantar los servicios

```bash
docker-compose up -d
```

Esto levanta:
- `backend` — FastAPI en puerto 8000
- `ollama` — Servidor LLM en puerto 11434
- `frontend` — Nginx sirviendo los archivos estáticos en puerto 80

### 4. Descargar el modelo de Ollama

La primera vez, hay que descargar el modelo LLM. Esto puede tardar varios minutos dependiendo de la conexión.

```bash
docker-compose exec ollama ollama pull llama3
```

Para un modelo más liviano (menor calidad, más rápido):
```bash
docker-compose exec ollama ollama pull mistral
# Y en .env: OLLAMA_MODEL=mistral
```

### 5. Verificar que todo funciona

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Verificar que el backend responde
curl http://localhost:8000/health

# Verificar que Ollama está listo
curl http://localhost:11434/api/tags
```

### 6. Abrir la aplicación

Abrir el navegador en `http://localhost`

### Comandos útiles

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (borra datos guardados)
docker-compose down -v

# Ver logs de un servicio específico
docker-compose logs -f backend

# Reiniciar solo el backend (por ejemplo, tras cambiar .env)
docker-compose restart backend

# Acceder al shell del contenedor backend
docker-compose exec backend bash

# Ejecutar tests
docker-compose exec backend pytest tests/ -v
```

---

## Opción B: Correr sin Docker (desarrollo local)

Para desarrollo activo cuando se quiere ver cambios en tiempo real.

### 1. Instalar dependencias del sistema (macOS)

```bash
# WeasyPrint necesita Cairo y Pango
brew install cairo pango gdk-pixbuf libffi

# Verificar
python3 -c "import weasyprint; print('WeasyPrint OK')"
```

### 1b. Instalar dependencias del sistema (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info
```

### 2. Crear entorno virtual e instalar dependencias Python

```bash
python3.11 -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Instalar y configurar Ollama

```bash
# Descargar e instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar el modelo
ollama pull llama3

# Verificar que está corriendo
ollama list
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env — cambiar OLLAMA_BASE_URL a http://localhost:11434
```

### 5. Levantar el backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Servir el frontend

En una terminal separada:
```bash
cd frontend
python3 -m http.server 3000
```

Abrir `http://localhost:3000`

---

## Opción C: Server Casero con Docker (producción local)

Para correr el agente en un servidor de la red local (NAS, Raspberry Pi 4, mini PC).

### Requisitos del servidor
- Linux (Ubuntu 22.04 recomendado)
- Docker + docker-compose instalados
- 8 GB RAM mínimo
- Accesible en la red local por IP o nombre de host

### 1. Preparar el servidor

```bash
# En el servidor
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Copiar el proyecto al servidor

```bash
# Desde tu máquina local
scp -r research-agent/ usuario@192.168.1.X:/home/usuario/
```

O clonar directamente desde el servidor si tiene acceso al repo.

### 3. Configurar y levantar

```bash
# En el servidor
cd research-agent
cp .env.example .env
# Editar .env según corresponda

docker-compose up -d
docker-compose exec ollama ollama pull llama3
```

### 4. Acceder desde la red local

```
http://192.168.1.X        ← Interfaz web
http://192.168.1.X:8000   ← API (para debug)
```

### Configurar para que levante automáticamente al reiniciar

```bash
# En el servidor
sudo systemctl enable docker

# En el directorio del proyecto
docker-compose up -d --restart=always
```

O con systemd:
```bash
# /etc/systemd/system/research-agent.service
[Unit]
Description=Research Agent
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/home/usuario/research-agent
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable research-agent
sudo systemctl start research-agent
```

---

## TODO: Deploy en la Nube (v2)

### Railway (recomendado para prototipo)

```
# Pendiente para v2
# Railway soporta Docker nativamente
# Costo estimado: ~$5-10/mes para uso moderado
# Nota: Ollama no corre en Railway — en la nube se usa OpenAI o Groq
```

Pasos generales:
1. Cambiar `LLM_PROVIDER=openai` o `LLM_PROVIDER=groq` en variables de entorno de Railway
2. Deployar con `railway up`
3. Configurar dominio custom

### Render

Similar a Railway, con tier gratuito con limitaciones (se duerme después de 15 min de inactividad).

---

## Persistencia de Datos

Los datos se guardan en volúmenes Docker montados en `./data/`:

```
data/
├── chroma/      ← Vector store (ChromaDB)
├── pdfs/        ← PDFs generados
└── db/          ← Base de datos SQLite (TODO v2)
```

**Para hacer backup:**
```bash
# Detener servicios
docker-compose stop

# Copiar directorio de datos
cp -r data/ backup-$(date +%Y%m%d)/

# Reiniciar
docker-compose start
```

---

## Troubleshooting

### "Connection refused" al llamar a Ollama

```bash
# Verificar que el servicio ollama está corriendo
docker-compose ps
docker-compose logs ollama

# Si no tiene el modelo descargado
docker-compose exec ollama ollama list
docker-compose exec ollama ollama pull llama3
```

### WeasyPrint falla al generar PDF

```bash
# Verificar dependencias del sistema en el contenedor
docker-compose exec backend python -c "import weasyprint"

# Si falla, reconstruir la imagen
docker-compose build --no-cache backend
```

### Error de memoria al correr llama3

Si el servidor tiene menos de 8 GB de RAM disponibles:
1. Cambiar a un modelo más liviano en `.env`: `OLLAMA_MODEL=tinyllama`
2. O usar Groq (gratuito, en la nube): `LLM_PROVIDER=groq`

### Puerto 80 ya está en uso

```bash
# Cambiar el puerto del frontend en docker-compose.yml
ports:
  - "8080:80"   # Cambiar 80 por cualquier puerto libre
```

Luego acceder en `http://localhost:8080`
