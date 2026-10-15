# Ticket: TICKET-002 - Frontend Scaffold & Design System Layer

* **ID:** TICKET-002
* **Título:** Andamiaje inicial del Frontend (Vite, React 18/19, TypeScript, Vanilla CSS Design System, Vitest)
* **Rama asignada:** `feature/frontend-scaffold`
* **Asignado a:** Frontend Developer
* **Revisor / QA:** QA & Security Tester
* **Estado:** done
* **Dependencias:** TICKET-001 (para alinear contratos de API)

---

## 1. Objetivo
Inicializar la estructura del frontend en `frontend/` utilizando Vite, React, TypeScript estricto, Design Tokens en Vanilla CSS moderno (Dark Mode, Glassmorphism, paleta HSL, tipografía moderna), configuración de ESLint, Prettier y Vitest, lockfile fijado (`package-lock.json`), y `frontend/.env.example`.

---

## 2. Archivos Afectados (Propiedad Exclusiva del Frontend Developer)
* `frontend/` (todo su contenido)
  - `frontend/package.json`
  - `frontend/package-lock.json`
  - `frontend/tsconfig.json`
  - `frontend/tsconfig.node.json`
  - `frontend/vite.config.ts`
  - `frontend/index.html`
  - `frontend/.env.example`
  - `frontend/src/`
    - `frontend/src/main.tsx`
    - `frontend/src/App.tsx`
    - `frontend/src/styles/tokens.css`
    - `frontend/src/styles/global.css`
    - `frontend/src/types/api.ts`
    - `frontend/src/services/apiClient.ts`
    - `frontend/src/components/Header.tsx`
    - `frontend/src/components/Footer.tsx`
  - `frontend/tests/`
    - `frontend/tests/App.test.tsx`

---

## 3. Criterios de Aceptación Técnicos
1. **Dependencias Fijadas y Lockfile:**
   - React y React DOM fijados.
   - Vite, TypeScript, ESLint, Prettier.
   - Vitest y React Testing Library para tests unitarios.
   - Generación y custodia de `package-lock.json`.
   - `npm audit` sin vulnerabilidades críticas o altas.
2. **Design Tokens & Estética Premium:**
   - Archivo `styles/tokens.css` definiendo variables CSS para:
     - Paleta de colores oscuros (`--bg-primary`, `--bg-surface`, `--bg-glass`, `--border-glass`).
     - Acentos armoniosos (`--accent-primary`, `--accent-hover`, `--accent-glow`).
     - Tipografía moderna (Google Font Outfit / Inter).
     - Efectos de Glassmorphism (`backdrop-filter: blur(12px)`).
3. **Cliente de API Desacoplado:**
   - `services/apiClient.ts` configurado para consumir `VITE_API_BASE_URL` (leída desde `.env`).
   - Sin llamadas a APIs de terceros directas desde el cliente.
4. **Archivo de Variables de Entorno:**
   - `frontend/.env.example` con únicamente:
     ```env
     VITE_API_BASE_URL=http://localhost:8000
     ```
   - Cero secretos o claves privadas en el frontend.
5. **Calidad y Tests:**
   - `npm run lint` pasando sin advertencias.
   - `npm run format:check` pasando.
   - `npm test` ejecutando pruebas con Vitest.
   - `npm run build` compilando el bundle estático en `dist/` sin errores de tipos de TypeScript.

---

## 4. Fuera de Alcance
- Nginx y Dockerfile del frontend (pertenecen a `feature/docker-env`).
- Componentes de búsqueda por imagen y resultados (pertenecen a `feature/result-ui`).

---

## 5. Guía de Verificación para QA
```bash
cd frontend
npm run lint
npm run format:check
npm test
npm audit
npm run build
```
