# Ticket: TICKET-009 - Security Hardening, Audit & Production Documentation

* **ID:** TICKET-009
* **Título:** Auditoría de Seguridad, Blindaje de Dependencias y Documentación Definitiva (README, SECURITY, ARCHITECTURE)
* **Rama asignada:** `feature/security-hardening`
* **Asignado a:** Security Engineer & Tech Lead
* **Revisor / QA:** QA & Security Tester
* **Estado:** done
* **Dependencias:** TICKET-001 a TICKET-008


---

## 1. Objetivo
Ejecutar la verificación final de seguridad integral del sistema AnimeFinder, incluyendo escaneo de vulnerabilidades en dependencias (`pip-audit` en backend y `npm audit` en frontend), verificación de políticas de CSP y cabeceras defensivas en Nginx, validación de mitigaciones de SSRF, DoS de memoria y privacidad de imágenes (no persistencia en disco ni logs de PII), y redacción de la documentación técnica y de operación de grado de producción (`README.md`, `docs/SECURITY.md` y `docs/ARCHITECTURE.md`).

---

## 2. Criterios de Aceptación Técnicos
1. **Auditoría de Vulnerabilidades (SAST / SCA):**
   - Ejecutar `pip-audit` dentro del contenedor del backend asegurando 0 vulnerabilidades críticas o altas.
   - Ejecutar `npm audit` en el entorno frontend asegurando 0 vulnerabilidades altas o críticas.
2. **Auditoría de Cabeceras HTTP y Aislamiento de Contenedores:**
   - Validar que Nginx responde con `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`.
   - Validar que los contenedores backend y frontend corren con usuarios sin privilegios (`appuser:10001` y `nginx`).
3. **Documentación de Seguridad (`docs/SECURITY.md`):**
   - Modelo de amenazas (STRIDE), políticas de reporte de vulnerabilidades, detalle de mitigaciones implementadas (magic bytes, EXIF stripping, memory semaphores, rate limiting en Redis, circuit breakers, sanitización anti-XSS con NH3).
4. **Documentación de Arquitectura (`docs/ARCHITECTURE.md`):**
   - Diagrama C4 / Mermaid con la topología de servicios (Nginx, FastAPI, Redis, trace.moe, AniList, Gemini).
   - Diagrama de secuencia del flujo de búsqueda por imagen y búsqueda textual con fallback.
   - Detalle de la política de caché, invalidación y manejo de cuotas.
5. **Documento Principal (`README.md`):**
   - Presentación del proyecto, tecnologías, características principales.
   - Guía de inicio rápido con un solo comando (`docker.ps1 up` / `docker compose up --build`).
   - Matriz de endpoints de la API con ejemplos de curl.
   - Variables de entorno documentadas.
   - Atribución obligatoria a trace.moe y AniList.

---

## 3. Archivos Involucrados
- `docs/SECURITY.md`
- `docs/ARCHITECTURE.md`
- `README.md`
- `docs/tickets/TICKET-009-security-hardening.md`
- `docs/tickets/QA-REPORT-TICKET-009.md`
