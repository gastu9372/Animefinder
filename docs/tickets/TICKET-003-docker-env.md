# Ticket: TICKET-003 - Docker Environment & Orchestration

* **ID:** TICKET-003
* **Título:** Entorno de Contenedores Docker Multi-Stage, Docker Compose con Healthchecks y Redis
* **Rama asignada:** `feature/docker-env`
* **Asignado a:** DevOps / Backend Developer
* **Revisor / QA:** QA & Security Tester
* **Estado:** done
* **Dependencias:** TICKET-001 (Backend Scaffold), TICKET-002 (Frontend Scaffold)

---

## 1. Objetivo
Configurar el entorno de ejecución local en contenedores para Backend (FastAPI), Frontend (Nginx + React) y Caché (Redis 7), cumpliendo con los estándares de producción: imágenes multi-stage, usuarios no-root, healthchecks en cada servicio, red interna aislada y scripts de desarrollo.

---

## 2. Criterios de Aceptación Técnicos
1. **Backend Dockerfile (`backend/Dockerfile`):**
   - Multi-stage build (builder + runner) con base ligera `python:3.12-slim`.
   - Creación y ejecución bajo usuario sin privilegios `appuser` (UID 10001).
   - Variables de entorno Python optimizadas (`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`).
   - `HEALTHCHECK` configurado contra `http://localhost:8000/api/v1/health`.
   - Archivo `backend/.dockerignore` excluyendo `.git`, `__pycache__`, `.venv`, `.pytest_cache`, `.env`.
2. **Frontend Dockerfile (`frontend/Dockerfile` & `frontend/nginx.conf`):**
   - Multi-stage build: Etapa 1 con `node:22-alpine` para compilar el bundle estático con `npm run build`; Etapa 2 con `nginx:alpine` para servir los activos.
   - `nginx.conf` configurado como Reverse Proxy dirigiendo el tráfico `/api/v1/` hacia el servicio `http://backend:8000/api/v1/` y resolviendo SPA routing (`try_files $uri /index.html`).
   - Headers de seguridad HTTP inyectados en Nginx (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy`).
   - `HEALTHCHECK` configurado para Nginx.
   - Archivo `frontend/.dockerignore` excluyendo `node_modules`, `dist`, `.env`.
3. **Orquestación con Docker Compose (`docker-compose.yml`):**
   - Servicios definidos: `backend`, `frontend`, `redis`.
   - Servicio `redis`: imagen oficial `redis:7-alpine` con healthcheck `redis-cli ping`.
   - Dependencias con condiciones: `backend` espera que `redis` esté `service_healthy`; `frontend` espera que `backend` esté `service_healthy`.
   - Red interna aislada `animefinder-network`.
   - Sin puertos innecesarios expuestos hacia el host (solo frontend: 80 y backend: 8000 opcional para dev).
4. **Comandos Estándar (`Makefile` & `scripts/`):**
   - `Makefile` con targets: `up`, `down`, `build`, `logs`, `test`.
   - Script helper para Windows PowerShell `scripts/docker.ps1`.
5. **Variables de Entorno Raíz (`.env.example`):**
   - `.env.example` en la raíz listo para copiar a `.env` y levantar todo con `docker compose up --build`.

---

## 3. Archivos Involucrados
- `backend/Dockerfile`
- `backend/.dockerignore`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `frontend/.dockerignore`
- `docker-compose.yml`
- `.env.example` (raíz)
- `Makefile`
- `scripts/docker.ps1`
- `docs/tickets/TICKET-003-docker-env.md`

---

## 4. Guía de Verificación para QA
```powershell
# 1. Copiar .env.example
Copy-Item .env.example .env

# 2. Levantar la aplicación con Docker Compose
docker compose up --build -d

# 3. Verificar estado de los contenedores y healthchecks
docker compose ps
# Esperado: backend (healthy), frontend (healthy), redis (healthy)

# 4. Verificar respuesta de healthcheck vía Nginx (puerto 80)
curl http://localhost/api/v1/health
# Esperado: HTTP 200 {"status":"healthy","version":"0.1.0", ...}

# 5. Detener el entorno
docker compose down
```
