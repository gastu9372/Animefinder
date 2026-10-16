# Ticket: TICKET-007 - Text Description Search (Gemini LLM & AniList Fallback)

* **ID:** TICKET-007
* **Título:** Servicio y Endpoint de Búsqueda por Descripción Libre con Gemini Reasoning y Fallback en AniList
* **Rama asignada:** `feature/text-search`
* **Asignado a:** Backend Developer
* **Revisor / QA:** QA & Security Tester
* **Estado:** done
* **Dependencias:** TICKET-005 (Anime Provider Layer), TICKET-006 (Image Search)


---

## 1. Objetivo
Implementar la búsqueda inteligente de anime por descripción libre de trama, personajes o escenas. Integrar el razonamiento semántico de Google Gemini mediante Structured Outputs (JSON Schema), validación estricta anti-alucinaciones contra AniList GraphQL (`TITLE_MATCH_MIN_SCORE = 0.70`), degradación elegante automática a búsqueda textual en AniList si no hay API key o se agota el tope diario (`LLM_DAILY_CALL_CAP`), sanitización de textos y almacenamiento en caché Redis.

---

## 2. Criterios de Aceptación Técnicos
1. **Adaptador Gemini LLM (`src/providers/gemini_ai.py`):**
   - Utiliza el SDK oficial `google-genai`.
   - Generación estructurada con esquema Pydantic: `anime_title: str`, `confidence_level: Literal["high", "medium", "low"]`, `match_reason: str`.
   - Respeto del tope diario de llamadas en Redis (`LLM_DAILY_CALL_CAP = 200`).
   - Manejo de excepciones: si no hay clave configurada o la API externa falla, levanta excepción controlada para activar el fallback.
2. **Servicio Orquestador (`src/services/text_search_service.py`):**
   - Normalización de entrada: recorte a máx 500 caracteres y strip de espacios.
   - Rate limit por IP en Redis (10 req/min).
   - Caché en Redis con clave `cache:text:<sha256(texto_normalizado)>` (TTL 48h).
   - Filtrado anti-alucinaciones: cálculo de similitud con `rapidfuzz` entre el título inferido por el LLM y los títulos retornados por AniList. Si el puntaje es menor a `TITLE_MATCH_MIN_SCORE` (0.70), se descarta el candidato e incrementa `filtered_count`.
   - Modo Fallback automático: si Gemini no está disponible, realiza búsqueda directa por términos en AniList GraphQL marcando `search_mode = "fallback"`.
   - Sanitización de `match_reason` eliminando cualquier etiqueta o inyección HTML.
   - Filtrado de contenido adulto según `ADULT_CONTENT_POLICY`.
3. **Endpoint `POST /api/v1/search/text` (`src/api/v1/endpoints/search_text.py`):**
   - Valida el payload JSON: `{ "description": str (3..500 chars), "limit": int (1..10) }`.
   - Retorna contrato canónico con `search_mode` (`"llm"` o `"fallback"`), `filtered_count`, `processing_time_ms` y `results`.
4. **Testing de Integración y Casos Borde (`tests/unit/test_text_search.py`):**
   - Test de flujo LLM exitoso con validación de título.
   - Test de descarte de título alucinado (< 0.70).
   - Test de fallback automático a AniList ante ausencia de `GEMINI_API_KEY`.
   - Test de caché en Redis para texto idéntico.

---

## 3. Archivos Involucrados
- `backend/src/providers/gemini_ai.py`
- `backend/src/services/text_search_service.py`
- `backend/src/api/v1/endpoints/search_text.py`
- `backend/src/api/v1/router.py`
- `backend/tests/unit/test_text_search.py`
- `docs/tickets/TICKET-007-text-search.md`
