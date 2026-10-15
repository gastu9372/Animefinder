# Ticket: TICKET-001 - Backend Scaffold & Core Layer

* **ID:** TICKET-001
* **Título:** Andamiaje inicial del Backend (FastAPI, Settings, Errores RFC 7807, Health Endpoint y Tooling)
* **Rama asignada:** `feature/backend-scaffold`
* **Asignado a:** Backend Developer
* **Revisor / QA:** QA & Security Tester
* **Estado:** in progress
* **Dependencias:** Ninguna (Ticket raíz del Backend)

---

## 1. Objetivo
Inicializar la estructura del backend en `backend/` con FastAPI, Python 3.12, dependencias exactas fijadas, validación de variables de entorno con `pydantic-settings` (fail-fast al arrancar), stub de manejador de errores estándar RFC 7807, CORS configurable, desactivación de documentación Swagger en entornos productivos, logging estructurado en JSON sin PII, y endpoint `/api/v1/health` mínimo.

---

## 2. Archivos Afectados (Propiedad Exclusiva del Backend Developer)
* `backend/` (todo su contenido)
  - `backend/pyproject.toml`
  - `backend/requirements.txt`
  - `backend/.env.example`
  - `backend/src/`
    - `backend/src/main.py`
    - `backend/src/core/config.py`
    - `backend/src/core/exceptions.py`
    - `backend/src/core/logging.py`
    - `backend/src/core/security.py`
    - `backend/src/api/v1/router.py`
    - `backend/src/api/v1/endpoints/health.py`
  - `backend/tests/`
    - `backend/tests/conftest.py`
    - `backend/tests/unit/test_config.py`
    - `backend/tests/unit/test_health.py`
    - `backend/tests/unit/test_magic_bytes.py`
* Raíz: `.pre-commit-config.yaml` (propiedad compartida inicializada por Backend Developer).

---

## 3. Criterios de Aceptación Técnicos
1. **Dependencias Fijadas con Versiones Exactas:**
   - Framework & Servidor: `fastapi==0.115.2`, `uvicorn[standard]==0.32.0`, `python-multipart==0.0.12`.
   - Validación & Configuración: `pydantic==2.9.2`, `pydantic-settings==2.6.0`.
   - Clientes HTTP & Async: `httpx==0.27.2`.
   - Procesamiento de Imágenes: `pillow==11.0.0`, `filetype==1.2.0` (o validador nativo según ADR 0001).
   - Resiliencia & Caché: `redis==5.2.0`, `tenacity==9.0.0`, `pybreaker==1.2.0`.
   - Algoritmos de Texto & Sanitización: `rapidfuzz==3.10.1`, `nh3==0.2.18`.
   - LLM SDK Oficial: `google-genai==0.1.1`.
   - Testing & Calidad: `pytest==8.3.3`, `pytest-asyncio==0.24.0`, `pytest-cov==5.0.0`, `respx==0.21.1`, `fakeredis[lua]==2.25.1`, `pip-audit==2.7.3`, `mypy==1.12.1`, `ruff==0.7.0`, `pre-commit==4.0.1`.
2. **Fail-Fast en Configuración:**
   - La clase `Settings` en `src/core/config.py` debe validar todas las variables obligatorias al instanciarse. Si falta una variable crítica (o tiene un valor no permitido), la aplicación debe lanzar un error y abortar el arranque de inmediato.
   - Test unitario específico (`test_config.py`) que verifique que el inicio falla si faltan valores requeridos.
3. **CORS Configurable:**
   - `CORS_ORIGINS` leído desde las variables de entorno (separado por comas) y configurado mediante `CORSMiddleware`.
4. **Protección de Endpoints de Documentación:**
   - Si `ENVIRONMENT == "production"`, `docs_url`, `redoc_url` y `openapi_url` deben ser `None`.
5. **Logging Estructurado sin PII:**
   - Logger configurado en formato JSON que no imprima datos binarios, IPs completas ni textos sensibles.
6. **Manejo Centralizado de Errores RFC 7807:**
   - Middleware / exception handlers para `AppException` y errores HTTP retornando `{"type": "...", "title": "...", "status": ..., "detail": "...", "code": "..."}`.
7. **Health Check Mínimo:**
   - Endpoint `GET /api/v1/health` que retorne:
     ```json
     {
       "status": "healthy",
       "timestamp": "2026-10-15T19:50:00Z",
       "version": "0.1.0"
     }
     ```
   - No incluye datos de Redis ni trace.moe en este ticket preliminar.
8. **Configuración de Variables de Entorno:**
   - `backend/.env.example` debe contener todas las variables del plan v1.2 con valores de ejemplo claros y sin secretos.
9. **Auditoría de Seguridad y Calidad:**
   - `ruff check .` limpio.
   - `ruff format --check .` limpio.
   - `mypy src tests` con tipado estricto sin errores.
   - `pip-audit` pasando sin vulnerabilidades conocidas.

---

## 4. Fuera de Alcance
- Dockerfiles y docker-compose (pertenecen a `feature/docker-env`).
- Pipeline de GitHub Actions (pertenece a `feature/ci-base`).
- Conexión real a trace.moe o AniList (pertenece a `feature/anime-provider-layer`).
- Búsqueda real de imágenes y texto (pertenece a `feature/image-search` y `feature/text-search`).

---

## 5. Guía de Verificación para QA
El agente de QA debe ejecutar los siguientes comandos y validar los resultados esperados:

```bash
# 1. Linting y Formateo
ruff check backend/
ruff format --check backend/

# 2. Tipado Estático
mypy backend/src backend/tests

# 3. Auditoría de Seguridad de Dependencias
pip-audit -r backend/requirements.txt

# 4. Suite de Tests Unitarios
pytest backend/tests/ -v --cov=backend/src

# 5. Ejecución del Servidor y Verificación del Endpoint
uvicorn src.main:app --app-dir backend --port 8000
curl http://localhost:8000/api/v1/health
# Esperado: HTTP 200 con {"status":"healthy","version":"0.1.0", ...}
```
