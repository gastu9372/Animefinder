# 🎌 AnimeFinder

> **Plataforma web de ingeniería profesional para la identificación instantánea de animes por imagen y descripción semántica libre.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-Multi--stage-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D.svg?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20%7C%20Vitest-success.svg?style=flat)](https://github.com)

---

## ✨ Características Principales

1. **Búsqueda Inversa por Imagen (Reverse Image Search):**
   - Identificación de fotogramas exactos de series y películas mediante **trace.moe** e integración canónica con **AniList GraphQL v2**.
   - Carga ágil mediante **Drag & Drop**, selector de archivos o pegado directo desde el portapapeles con <kbd>Ctrl</kbd> + <kbd>V</kbd>.
   - Muestra porcentaje exacto de similitud, número de episodio, timestamp formateado (`MM:SS`) y reproductor de video de vista previa.

2. **Búsqueda Inteligente por Descripción Libre:**
   - Razonamiento semántico mediante **Google Gemini** con Structured Outputs (*Pydantic Schema*).
   - Filtro anti-alucinaciones estricto con **RapidFuzz** (`TITLE_MATCH_MIN_SCORE = 0.70`) para corroborar la existencia de la obra en AniList.
   - **Degradación elegante automática (*graceful fallback*):** Si Gemini no está configurado o se agota el tope diario (`LLM_DAILY_CALL_CAP`), conmuta de forma transparente a búsqueda textual directa en AniList sin interrumpir la experiencia.

3. **Arquitectura y Blindaje de Grado Producción:**
   - **Cero Persistencia de Imágenes:** Los buffers se validan en memoria RAM (mediante inspección pura de Magic Bytes para JPEG, PNG y WebP) y se descartan inmediatamente tras el procesamiento.
   - **Protección contra DoS de Memoria:** Límite estricto de 10 Megapíxeles en Pillow (`MAX_IMAGE_PIXELS`) y semáforo de concurrencia de procesamiento.
   - **Caché Inteligente en Redis (TTL 48h):** Indexación SHA-256 excluyendo URLs de video temporales.
   - **Protección de Contenido Adulto (+18):** Filtro visual con efecto de desenfoque (*blur*) y advertencia de revelación voluntaria.
   - **Contenedores sin Privilegios:** Ejecución bajo usuarios no-root (`appuser:10001` y `nginx`).
   - **Cabeceras de Seguridad HTTP:** Nginx configurado con Content-Security-Policy (CSP), `X-Frame-Options: DENY`, `nosniff` y `X-XSS-Protection`.

---

## 🚀 Inicio Rápido con Docker

La aplicación está completamente dockerizada y lista para ejecutarse en cualquier entorno con Docker Desktop.

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/AnimeFinder.git
cd AnimeFinder
```

### 2. Configurar variables de entorno (Opcional)
Si deseás habilitar el razonamiento semántico con IA, obtené una clave gratuita en [Google AI Studio](https://aistudio.google.com/) y agregala al archivo `.env`:
```env
GEMINI_API_KEY=tu_clave_de_gemini_aqui
```
*(Si no configurás ninguna clave, el sistema operará automáticamente en modo de fallback con AniList).*

### 3. Levantar los servicios

En **Windows (PowerShell)**:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker.ps1 up
```

En **Linux / macOS**:
```bash
docker compose up -d --build
```

### 4. Abrir en el navegador
- **Frontend Web:** [http://localhost](http://localhost) (Puerto 80)
- **API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🛠 Comandos de Utilidad (`scripts/docker.ps1`)

| Acción | Comando PowerShell | Descripción |
| :--- | :--- | :--- |
| **Iniciar App** | `.\scripts\docker.ps1 up` | Construye y levanta Frontend, Backend y Redis en segundo plano. |
| **Detener App** | `.\scripts\docker.ps1 down` | Detiene y remueve los contenedores activos. |
| **Ver Estado** | `.\scripts\docker.ps1 ps` | Lista el estado de salud (*healthcheck*) de cada contenedor. |
| **Ver Logs** | `.\scripts\docker.ps1 logs` | Muestra el flujo en tiempo real de logs de los servicios. |
| **Ejecutar Tests** | `.\scripts\docker.ps1 test` | Ejecuta la suite completa de 29 pruebas unitarias con Pytest en Docker. |
| **Auditar Seguridad** | `.\scripts\docker.ps1 audit` | Ejecuta `pip-audit` sobre las dependencias del contenedor de backend. |
| **Verificar Usuario** | `.\scripts\docker.ps1 whoami` | Verifica la ejecución bajo el usuario no-root `appuser:10001`. |

---

## 📡 Referencia de la API REST

Todos los errores siguen el estándar internacional **RFC 7807 (Problem Details)**.

### 1. Búsqueda por Captura de Escena
```bash
POST /api/v1/search/image
Content-Type: multipart/form-data
Body: file=@captura.jpg
```

**Ejemplo de Respuesta (200 OK):**
```json
{
  "query_type": "image",
  "search_mode": "trace.moe",
  "cached": false,
  "filtered_count": 0,
  "processing_time_ms": 680,
  "results": [
    {
      "id": 1535,
      "title": {
        "romaji": "Death Note",
        "english": "Death Note",
        "native": "デスノート"
      },
      "cover_image": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx1535.jpg",
      "synopsis": "Light Yagami es un estudiante sobresaliente...",
      "year": 2006,
      "format": "TV",
      "is_adult": false,
      "confidence_percentage": 0.985,
      "confidence_level": "high",
      "match_reason": null,
      "scene_info": {
        "episode": 1,
        "timestamp_seconds": 312.5,
        "timestamp_formatted": "05:12",
        "preview_video_url": "https://api.trace.moe/video/..."
      }
    }
  ]
}
```

### 2. Búsqueda por Descripción Libre
```bash
POST /api/v1/search/text
Content-Type: application/json
Body: { "description": "un chico que encuentra un cuaderno que mata personas", "limit": 5 }
```

**Ejemplo de Respuesta (200 OK):**
```json
{
  "query_type": "text",
  "search_mode": "llm",
  "cached": true,
  "filtered_count": 0,
  "processing_time_ms": 0,
  "results": [
    {
      "id": 1535,
      "title": {
        "romaji": "Death Note",
        "english": "Death Note",
        "native": "デスノート"
      },
      "cover_image": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx1535.jpg",
      "synopsis": "Light Yagami finds a supernatural notebook...",
      "year": 2006,
      "format": "TV",
      "is_adult": false,
      "confidence_percentage": null,
      "confidence_level": "high",
      "match_reason": "El protagonista invocado encuentra el Death Note y elimina criminales.",
      "scene_info": null
    }
  ]
}
```

---

## 🧪 Pruebas Automatizadas

AnimeFinder cuenta con cobertura de pruebas automatizadas en ambas capas:

### Backend (Python / Pytest)
```bash
# Dentro del contenedor Docker:
powershell -ExecutionPolicy Bypass -File scripts\docker.ps1 test

# O localmente:
cd backend && pytest --cov=src
```
- **29/29 tests pasando al 100%:** Detección de magic bytes, validación de schemas Pydantic, rate limiters, fallback de AniList, circuito de Gemini, descarte anti-alucinaciones, y extracción segura de IP.

### Frontend (TypeScript / Vitest)
```bash
cd frontend && npm test -- --run
```
- **8/8 tests pasando al 100%:** Renderizado de tarjetas de anime, verificación de badges, desenfoque de contenido adulto, temporizador de reintento en errores RFC 7807 y conmutación de pestañas.

---

## 📜 Atribuciones y Términos de Servicio

Este proyecto respeta estrictamente los Términos de Servicio de las fuentes utilizadas:
- **[trace.moe](https://trace.moe):** Motor de búsqueda inversa de anime desarrollado por Soruly. Cumple con la cuota de concurrencia y límites por IP.
- **[AniList API](https://anilist.co):** Provisión de metadatos oficiales y portadas en alta resolución. Uso no comercial respetando la ventana de rate limits degradados mediante batching GraphQL.
- **[Google Gemini](https://ai.google.dev):** Modelos de lenguaje semántico para extracción estructurada de entidades.

---
*Desarrollado con arquitectura profesional y buenas prácticas de ingeniería de software.*
