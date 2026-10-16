# Reporte de QA: Verificación de TICKET-007 (Text Description Search con Gemini & Fallback AniList)

* **Ticket Asociado:** TICKET-007
* **Rama:** `feature/text-search`
* **Agente Evaluador:** QA & Security Tester
* **Fecha:** Octubre 2026
* **Resultado:** APROBADO (PASS)

---

## 1. Alcance de la Revisión
Se auditó la implementación de búsqueda por descripción textual libre en `src/providers/gemini_ai.py`, `src/services/text_search_service.py` y `src/api/v1/endpoints/search_text.py`:
- Integración con Google Gemini usando `google-genai` con Structured Outputs (Pydantic schema).
- Control de cuota diaria en Redis (`LLM_DAILY_CALL_CAP = 200`) para prevenir sobrecostos o agotamiento de cuota.
- Sanitización estricta anti-XSS en `match_reason` mediante `nh3`.
- Filtro anti-alucinaciones con `rapidfuzz` comparando títulos devueltos por LLM con AniList (`TITLE_MATCH_MIN_SCORE = 0.70`). Los candidatos que no superan el umbral se descartan y se contabilizan en `filtered_count`.
- Degradación elegante automática a búsqueda textual directa en AniList GraphQL cuando Gemini no está configurado o falla, marcando `search_mode = "fallback"`.
- Caché SHA-256 en Redis por 48 horas para textos idénticos.
- Endpoint `POST /api/v1/search/text` con validaciones de longitud (3 a 500 caracteres) y límite de resultados.

---

## 2. Matriz de Validación de QA

| Prueba de Verificación | Método / Comando | Resultado Observado | Estado |
| :--- | :--- | :--- | :--- |
| **Similitud de Títulos Anti-Alucinación** | `test_compute_title_similarity` | Distingue coincidencias exactas (1.0), variaciones tipográficas (>0.85) y animes no relacionados (<0.40). | ✅ PASS |
| **Manejo de Gemini No Configurado** | `test_gemini_provider_unconfigured` | Dispara `LLMNotConfiguredError` inmediatamente para activar el fallback. | ✅ PASS |
| **Control de Tope Diario en Redis** | `test_gemini_provider_daily_cap_exceeded` | Superadas las 200 llamadas en Redis, levanta `LLMDailyCapReachedError`. | ✅ PASS |
| **Flujo Exitoso con Gemini y Sanitización** | `test_text_search_llm_success_flow` | Infiere anime, limpia HTML (`<b>`) con `nh3`, retorna nivel "high". | ✅ PASS |
| **Descarte de Candidato Alucinado** | `test_text_search_anti_hallucination_discard` | Título no coincidente con AniList es descartado e incrementa `filtered_count = 1`. | ✅ PASS |
| **Fallback Transparente a AniList** | `test_text_search_fallback_on_unconfigured_llm` | Sin clave LLM, busca directamente en AniList, `search_mode = "fallback"`. | ✅ PASS |
| **Caché en Redis de Texto Idéntico** | `test_text_search_caching` | Segunda consulta exacta se resuelve desde Redis sin invocar al proveedor. | ✅ PASS |
| **Validación de Parámetros en Endpoint** | `test_text_search_endpoint_validation` | Longitud < 3 caracteres o límite > 10 responden con HTTP 422. | ✅ PASS |
| **Prueba en Vivo a través de Nginx** | `curl.exe http://localhost:80/api/v1/search/text` | Consulta real "death note" responde con animes canónicos y se cachea (`cached: true`). | ✅ PASS |
| **Ejecución Total de Suite en Docker** | `docker compose exec backend pytest` | 29/29 tests pasando al 100% en 0.39s con cobertura 72%. | ✅ PASS |

---

## 3. Conclusión de QA
El servicio de búsqueda por texto cumple rigurosamente con los requisitos de robustez, seguridad, fallback transparente y protección de cuotas. Se autoriza el merge de `feature/text-search` a `develop`.
