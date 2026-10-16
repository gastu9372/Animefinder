# ==============================================================================
# Multi-Stage Dockerfile para AnimeFinder Backend (FastAPI)
# Usuario No-Root (appuser:10001) para máxima seguridad en producción
# ==============================================================================

# --- Etapa 1: Builder de Dependencias ---
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Etapa 2: Runner de Producción ---
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar librerías Python instaladas desde builder
COPY --from=builder /install /usr/local

# Crear usuario y grupo sin privilegios
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser && \
    chown -R appuser:appgroup /app

# Copiar configuración y código fuente
COPY --chown=appuser:appgroup pyproject.toml /app/
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup tests/ /app/tests/

# Cambiar al usuario no-root
USER appuser:appgroup

EXPOSE 8000

# Healthcheck interno del contenedor
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
