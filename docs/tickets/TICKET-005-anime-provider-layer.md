# Ticket: TICKET-005 - Anime Provider Layer (trace.moe & AniList Batching)

* **ID:** TICKET-005
* **Título:** Capa de Proveedores desacoplada con Adaptadores para trace.moe y AniList GraphQL
* **Rama asignada:** `feature/anime-provider-layer`
* **Asignado a:** Backend Developer
* **Revisor / QA:** QA & Security Tester
* **Estado:** in progress
* **Dependencias:** TICKET-001, TICKET-003, TICKET-004

---

## 1. Objetivo
Implementar la capa de abstracción de proveedores (`src/providers/`) siguiendo el patrón Provider/Adapter. Desarrollar las interfaces abstractas y los adaptadores concretos para `trace.moe` (concurrencia 1, sync con `/me`, deduplicación por anime) y `AniList GraphQL` (batching con aliases, sanitización de HTML/spoilers con `nh3`, respeto a `Retry-After` y caché en Redis).

---

## 2. Criterios de Aceptación Técnicos
1. **Interfaces Abstractas (`src/providers/base.py`):**
   - `BaseImageSearchProvider`: método `search_by_image(image_bytes: bytes) -> list[RawImageMatch]`.
   - `BaseMetadataProvider`: método `get_anime_batch(anilist_ids: list[int]) -> dict[int, CanonicalAnime]`.
2. **Adaptador trace.moe (`src/providers/trace_moe.py`):**
   - Llamada HTTP POST con buffer binario hacia `https://api.trace.moe/search`.
   - Sincronización con `GET /me` para comprobar saldo real y concurrencia.
   - Diferenciación del HTTP 402: distingue `Concurrency limit exceeded` (reintento corto) de `Search quota depleted` (bloqueo y aviso).
   - Deduplicación de escenas: agrupa por `anilist_id` quedándose exclusivamente con el fotograma de mayor similitud (`similarity`).
   - Límite de concurrencia coordinado con Redis (`TRACEMOE_MAX_CONCURRENCY=1`).
3. **Adaptador AniList GraphQL (`src/providers/anilist.py`):**
   - Consulta GraphQL en **UNA sola petición con aliases** para lotes de animes:
     ```graphql
     query GetBatch($ids: [Int]) {
       Page {
         media(id_in: $ids, type: ANIME) {
           id
           title { romaji english native }
           coverImage { extraLarge large }
           description(asHtml: false)
           seasonYear
           startDate { year }
           format
           isAdult
         }
       }
     }
     ```
   - Sanitización de sinopsis: limpieza de cualquier residuo HTML y remoción de spoilers `~!... spoiler ...!~` utilizando `nh3` y regex.
   - Respeto estricto del header `Retry-After` ante 429 de AniList.
   - Caché en Redis de metadatos canónicos con clave `anime:meta:<id>` y TTL de 48 horas.
4. **Dominio Canónico (`src/domain/models.py`):**
   - Modelos Pydantic para `CanonicalAnime`, `RawImageMatch`, `SceneInfo`, `TitleInfo`.
5. **Testing con Mocks (`tests/unit/test_providers.py`):**
   - Mock con `respx` de respuestas de trace.moe y AniList.
   - Cobertura de deduplicación de múltiples frames del mismo anime.
   - Cobertura de discriminación de error 402 de trace.moe.
   - Cobertura de sanitización de sinopsis con spoilers.

---

## 3. Archivos Involucrados
- `backend/src/domain/models.py`
- `backend/src/providers/base.py`
- `backend/src/providers/trace_moe.py`
- `backend/src/providers/anilist.py`
- `backend/src/core/redis.py`
- `backend/tests/unit/test_providers.py`
- `docs/tickets/TICKET-005-anime-provider-layer.md`
