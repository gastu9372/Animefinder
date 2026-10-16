# Arquitectura del Sistema - AnimeFinder

Este documento describe la arquitectura técnica, los flujos de datos y los patrones de resiliencia implementados en **AnimeFinder**.

---

## 1. Topología del Sistema

```mermaid
graph TD
    Client["Navegador Web (SPA React 18)"]
    Nginx["Nginx Reverse Proxy & Static Host (Puerto 80)"]
    FastAPI["FastAPI Backend (Puerto 8000)"]
    Redis["Redis 7 (Caché, Rate Limiter & Concurrencia)"]
    
    TraceMoe["trace.moe API (Reverse Image Search)"]
    AniList["AniList GraphQL API v2 (Metadata Canónica)"]
    Gemini["Google Gemini AI (Semantic Reasoning)"]

    Client -->|HTTP / SPA Estáticos| Nginx
    Client -->|POST /api/v1/*| Nginx
    Nginx -->|Proxy Pass /api/v1/| FastAPI
    
    FastAPI <-->|Rate Limit / Caché TTL / Semáforos| Redis
    FastAPI -->|Fotograma JPEG| TraceMoe
    FastAPI -->|Query GraphQL Batching| AniList
    FastAPI -->|Structured JSON Prompt| Gemini
```

---

## 2. Flujos de Secuencia de Búsqueda

### 2.1 Búsqueda Inversa por Imagen (`POST /api/v1/search/image`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuario
    participant FE as Frontend (React)
    participant API as FastAPI Backend
    participant R as Redis
    participant TM as trace.moe
    participant AL as AniList GraphQL

    User->>FE: Sube imagen (Drag&Drop, File, Ctrl+V)
    FE->>FE: Valida tipo (JPEG/PNG/WebP) y tamaño (<= 8MB)
    FE->>API: POST /api/v1/search/image (Multipart)
    API->>API: Valida Magic Bytes en memoria (Python puro)
    API->>R: Verifica Rate Limit (10/min, 10/día por IP)
    API->>API: Stripping EXIF y compresión a JPEG (asyncio.to_thread)
    API->>R: Adquiere semáforo distribuido (concurrency: 1)
    API->>TM: POST /search (Imagen JPEG)
    TM-->>API: 200 OK con anilist_id, episodio, timestamp y video
    API->>R: Libera semáforo
    API->>AL: Batching GraphQL Query (anilist_id)
    AL-->>API: Portada HD, sinopsis, títulos, año, formato, isAdult
    API->>API: Sanitiza sinopsis (nh3) y excluye preview_video_url de caché
    API->>R: Almacena en caché SHA-256 (TTL 48h)
    API-->>FE: 200 OK con AnimeResult canónico
    FE-->>User: Tarjeta de anime con confianza %, episodio y reproductor
```

### 2.2 Búsqueda Textual Libre con Fallback (`POST /api/v1/search/text`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuario
    participant FE as Frontend (React)
    participant API as FastAPI Backend
    participant R as Redis
    participant GM as Google Gemini
    participant AL as AniList GraphQL

    User->>FE: Escribe descripción (ej: "chico con cuaderno de muerte")
    FE->>API: POST /api/v1/search/text
    API->>R: Verifica Rate Limit (10/min) y Caché cache:text:<sha256>
    alt Cache Hit
        R-->>API: Payload JSON almacenado
        API-->>FE: 200 OK (cached: true, 0ms)
    else Cache Miss
        alt Gemini Configurado y Cuota Disponible (< 200 llamadas/día)
            API->>GM: generate_content(prompt, schema=LLMStructuredOutput)
            GM-->>API: Lista de candidatos: [{anime_title, confidence_level, match_reason}]
            loop Para cada candidato
                API->>AL: search_anime_by_title(candidate.anime_title)
                AL-->>API: Metadatos oficiales de AniList
                API->>API: Calcula similitud con RapidFuzz (score >= 0.70)
                Note over API: Si score < 0.70 descarta (anti-alucinación)
            end
            API->>API: Sanitiza match_reason con nh3
            API->>R: Guarda en caché por 48 horas
            API-->>FE: 200 OK (search_mode: "llm")
        else Error de Gemini o Sin Clave
            API->>AL: Búsqueda textual directa en GraphQL
            AL-->>API: Lista de animes canónicos
            API->>R: Guarda en caché por 48 horas
            API-->>FE: 200 OK (search_mode: "fallback")
        end
    end
    FE-->>User: Tarjetas con justificación de IA o aviso de fallback
```

---

## 3. Principios de Resiliencia y Mitigación de Cuotas

1. **Gestión de Cuota de trace.moe:**
   - La API gratuita de trace.moe asigna 100 consultas por cada 24 horas móviles por IP y concurrencia máxima 1.
   - El backend sincroniza `quota` y `quotaUsed` dinámicamente desde `/me` al inicio y tras errores 402.
   - El semáforo en Redis coordina las solicitudes para evitar saturación y colas 503.
2. **Degradación de AniList GraphQL:**
   - AniList se encuentra en modo degradado documentado a 30 req/min.
   - AnimeFinder implementa batching automático en 1 única petición con alias para múltiples IDs de anime.
   - Respeta estrictamente la cabecera `Retry-After` ante códigos 429.
   - Metadatos estables se almacenan en caché de Redis durante 48 horas.
3. **Protección de Presupuesto en LLM:**
   - `LLM_DAILY_CALL_CAP = 200` garantiza un límite rígido diario en Redis.
   - En caso de superarse el tope o no contar con `GEMINI_API_KEY`, el sistema conmuta automáticamente a búsqueda directa en AniList sin interrumpir el servicio al usuario.
