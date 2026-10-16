# Ticket: TICKET-006 - Image Search Service & Endpoint

* **ID:** TICKET-006
* **Título:** Servicio y Endpoint de Búsqueda Inversa por Imagen (`POST /api/v1/search/image`)
* **Rama asignada:** `feature/image-search`
* **Asignado a:** Backend Developer
* **Revisor / QA:** QA & Security Tester
* **Estado:** done
* **Dependencias:** TICKET-005 (Anime Provider Layer)

---

## 1. Objetivo
Implementar la funcionalidad completa de búsqueda inversa por captura de anime: recepción multipart, validación estricta de magic bytes en Python puro, procesamiento asíncrono no bloqueante en threadpool con Pillow (respetando límite de 10M píxeles y strip de EXIF), semáforo de memoria (máx 4 imágenes simultáneas), rate limiting por IP (10/min y 10/día), orquestación con `TraceMoeProvider` y `AniListProvider`, filtrado de contenido adulto, caché por SHA-256 en Redis (excluyendo video previews expirables) y respuesta canónica.

---

## 2. Criterios de Aceptación Técnicos
1. **Endpoint `POST /api/v1/search/image`:**
   - Consume `multipart/form-data` con campo `file: UploadFile`.
   - Rechazo de archivos mayores a `MAX_IMAGE_SIZE_BYTES` (8 MB) con HTTP 400 (RFC 7807).
   - Validación de magic bytes: solo `image/jpeg`, `image/png`, `image/webp`. Si es otro formato o archivo corrupto/falso, retorna HTTP 415.
2. **Procesamiento Asíncrono Seguro en Memoria:**
   - Encapsulado en `asyncio.to_thread` para no bloquear el event loop.
   - Control de concurrencia con semáforo en memoria `IMAGE_PROCESSING_CONCURRENCY = 4`.
   - Pillow con `Image.MAX_IMAGE_PIXELS = 10_000_000` (anti decompression bomb).
   - Reescalado si excede 1280x720 y eliminación de metadatos EXIF.
   - Las imágenes **nunca se guardan en disco ni en base de datos**.
3. **Control de Cuotas y Rate Limiting en Redis:**
   - Límite por IP: 10 peticiones por minuto.
   - Límite diario por IP: 10 búsquedas de imagen por día (`IMAGE_SEARCH_PER_IP_PER_DAY`).
   - Si se supera, retorna HTTP 429 con `Retry-After`.
4. **Caché Exacta SHA-256:**
   - Clave en Redis `cache:image:<sha256>`.
   - Si existe en caché, retorna inmediatamente con `cached: true` y omite `preview_video_url` (o la marca como expirada).
   - Si es nueva, consulta a los proveedores y guarda con TTL de 72 horas.
5. **Enriquecimiento y Filtrado de Contenido Adulto:**
   - Cruce en batch con `AniListProvider`.
   - Si `ADULT_CONTENT_POLICY == "filter"` y el anime tiene `is_adult == True`, se descarta y se incrementa `filtered_count`.
   - Cálculo de confianza: `confidence_percentage = round(match.similarity * 100, 1)`, y nivel cualitativo `"high"`, `"medium"`, `"low"`.
6. **Testing de Integración y Casos Borde:**
   - Test de subida exitosa de fixture PNG/JPEG con enriquecimiento.
   - Test de rechazo de ejecutable camuflado con extensión `.jpg`.
   - Test de archivo que supera 8 MB.
   - Test de caché SHA-256.
   - Test de filtrado de contenido adulto.

---

## 3. Archivos Involucrados
- `backend/src/services/image_search_service.py`
- `backend/src/api/v1/endpoints/search_image.py`
- `backend/src/api/v1/router.py`
- `backend/tests/unit/test_image_search.py`
- `docs/tickets/TICKET-006-image-search.md`
