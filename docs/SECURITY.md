# Política de Seguridad y Blindaje de AnimeFinder

Este documento describe la arquitectura defensiva, las políticas de mitigación de riesgos y el proceso formal para el reporte de vulnerabilidades en **AnimeFinder**.

---

## 1. Modelo de Amenazas y Mitigaciones Implementadas

AnimeFinder procesa imágenes y texto no confiables provistos por usuarios anónimos en Internet. Las siguientes defensas están implementadas y verificadas activamente:

### 1.1 Protección de Memoria y Prevención de Descompresión DoS (Image Decompression Bombs)
- **Umbral de Píxeles:** Configuración estricta de `Image.MAX_IMAGE_PIXELS = 10_000_000` (10 Megapíxeles) en Pillow para neutralizar ataques de descompresión (*decompression bombs*).
- **Semáforo de Concurrencia de CPU:** `IMAGE_PROCESSING_CONCURRENCY = 4` restringe el número de imágenes procesadas en simultáneo en hilos de Python (`asyncio.to_thread`), protegiendo el pool de CPU del servidor.
- **Límite de Tamaño de Archivo:** Validación de `MAX_IMAGE_SIZE_BYTES = 8_388_608` (8 MB) antes de procesar el buffer en memoria.
- **Sin Persistencia en Disco:** Las imágenes cargadas se validan e inspeccionan exclusivamente en RAM y se descartan inmediatamente tras el envío a trace.moe. Nunca se escriben en el sistema de archivos del servidor.

### 1.2 Validación de Tipos de Archivo sin Dependencias de Sistema (ADR 0001)
- **Inspección de Magic Bytes Pura:** Validación estricta de firmas binarias de cabecera (JPEG `FF D8 FF`, PNG `89 50 4E 47`, WebP `52 49 46 46 ... 57 45 42 50`) en memoria mediante Python puro y `filetype`.
- **Eliminación de `libmagic`:** Se erradicó la dependencia C `libmagic` para evitar vulnerabilidades de desbordamiento de búfer y problemas de compatibilidad multiplataforma.
- **Sanitización de Metadatos:** Se eliminan todos los metadatos EXIF / GPS / perfiles ICC de las imágenes antes de procesarlas o reenviarlas.

### 1.3 Prevención de SSRF (Server-Side Request Forgery)
- **Sin URLs Arbitrarias de Entrada:** La aplicación no acepta URLs remotas provistas por usuarios para descargar imágenes. El cliente debe subir el archivo binario directamente.
- **Endpoints de Terceros Fijos:** El backend solo se comunica con URLs de API estrictamente declaradas en variables de entorno validadas con Pydantic (`https://api.trace.moe`, `https://graphql.anilist.co`, Google Gemini API).

### 1.4 Aislamiento de Red y Rate Limiting por IP
- **Aislamiento en Redis:** Ventana de 10 peticiones por minuto por IP para búsqueda de texto e imágenes, y ventana de 10 búsquedas de imagen por día por IP (`IMAGE_SEARCH_PER_IP_PER_DAY=10`).
- **Validación Segura de Proxies:** `extract_client_ip` solo confía en cabeceras `X-Forwarded-For` o `X-Real-IP` si la conexión TCP directa proviene de proxies autorizados (`TRUSTED_PROXIES` = `127.0.0.1, 172.16.0.0/12, 10.0.0.0/8`). Conexiones directas falsificadas son ignoradas.

### 1.5 Sanitización Anti-XSS y Salidas Estructuradas de IA
- **Motor Rust `nh3`:** Todas las sinopsis provenientes de AniList y explicaciones de Gemini (`match_reason`) son saneadas con `nh3.clean()`, eliminando cualquier inyección de etiquetas HTML o atributos JavaScript (`<script>`, `<iframe>`, `onclick`).
- **Structured Outputs en Gemini:** Uso de esquemas Pydantic rígidos (`response_schema=LLMStructuredOutput`) que fuerzan al LLM a devolver únicamente JSON sintácticamente válido, impidiendo *prompt injection* en la interfaz.
- **Filtro Anti-Alucinación:** Similitud con `rapidfuzz` (`TITLE_MATCH_MIN_SCORE = 0.70`) para verificar que el anime razonado por el modelo exista en el catálogo oficial de AniList.

### 1.6 Seguridad en Nginx y Cabeceras HTTP
El proxy inverso Nginx aplica de forma obligatoria:
```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'; img-src 'self' data: https://s4.anilist.co https://api.trace.moe; media-src 'self' https://api.trace.moe; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self';" always;
```

### 1.7 Mínimo Privilegio en Contenedores Docker
- **Backend:** Ejecuta con usuario sin privilegios `appuser` (UID: 10001, GID: 10001) con `/sbin/nologin`.
- **Frontend:** Ejecuta sobre `nginx:alpine` sirviendo estáticos estricto sin acceso a shell ni capacidades de root.

---

## 2. Reporte de Vulnerabilidades

Si descubrís una vulnerabilidad de seguridad en AnimeFinder:
1. **No abras un issue público en GitHub.**
2. Enviá un correo detallado a `security@animefinder.local` con:
   - Descripción de la vulnerabilidad y vector de ataque.
   - Pasos para reproducir (PoC o scripts curl).
   - Impacto estimado según CVSS v3.
3. El equipo responderá dentro de las 48 horas hábiles confirmando la recepción y coordinando el parche antes de cualquier divulgación pública.
