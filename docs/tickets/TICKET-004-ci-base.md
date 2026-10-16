# Ticket: TICKET-004 - CI Base Workflow (GitHub Actions)

* **ID:** TICKET-004
* **Título:** Pipeline de Integración Continua (CI) en GitHub Actions (Lint, Tests, Typecheck y Docker Build)
* **Rama asignada:** `feature/ci-base`
* **Asignado a:** DevOps / QA Specialist
* **Revisor / QA:** QA & Security Tester
* **Estado:** done
* **Dependencias:** TICKET-001, TICKET-002, TICKET-003

---

## 1. Objetivo
Implementar el pipeline automatizado de Integración Continua (CI) en `.github/workflows/ci.yml` para garantizar que todo cambio enviado a `develop` o `main` cumpla rigurosamente el Definition of Done (DoD): código formateado, sin advertencias de linter, tipos estáticos validados, pruebas unitarias aprobadas y construcción de imágenes Docker sin errores.

---

## 2. Criterios de Aceptación Técnicos
1. **Pipeline de Backend (`backend-ci`):**
   - Ejecuta en `ubuntu-latest` con Python 3.12.
   - Pasos:
     - Checkout del código.
     - Caché de pip.
     - Instalación de dependencias desde `backend/requirements.txt`.
     - Linter: `ruff check backend/`.
     - Formateo: `ruff format --check backend/`.
     - Tipado estático: `mypy backend/src backend/tests`.
     - Tests unitarios: `pytest backend/tests/ --cov=backend/src`.
2. **Pipeline de Frontend (`frontend-ci`):**
   - Ejecuta en `ubuntu-latest` con Node.js 22.
   - Pasos:
     - Checkout del código.
     - Instalación limpia con `npm ci` en `frontend/`.
     - Linter: `npm run lint`.
     - Formateo: `npm run format:check`.
     - Tests unitarios: `npm test` (Vitest).
     - Compilación estática: `npm run build`.
3. **Validación de Contenedores (`docker-build`):**
   - Valida la sintaxis y construcción de `backend/Dockerfile` y `frontend/Dockerfile` mediante `docker compose build`.
4. **Disparadores (Triggers):**
   - Ejecución automática en `push` y `pull_request` sobre ramas `main` y `develop`.

---

## 3. Archivos Involucrados
- `.github/workflows/ci.yml`
- `docs/tickets/TICKET-004-ci-base.md`
