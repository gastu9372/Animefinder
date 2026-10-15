# ADR 0001: Validación de Magic Bytes en Python Puro vs. libmagic

* **Estado:** Aceptado
* **Fecha:** Octubre 2026
* **Decisores:** Tech Lead / PM

## Contexto
El sistema requiere validar que los archivos subidos al endpoint de búsqueda por imagen sean efectivamente imágenes válidas en formato JPEG, PNG o WebP, verificando su firma binaria (magic bytes) y no solo la extensión de archivo o el encabezado HTTP `Content-Type` enviado por el cliente (que puede ser fácilmente falsificado).

Históricamente se ha utilizado la librería `python-magic`, la cual es un wrapper de la biblioteca nativa en C `libmagic`.

## Problema
`python-magic` presenta fricciones operativas significativas:
1. En Windows requiere binarios DLL específicos (`python-magic-bin`), lo cual suele fallar o requerir configuraciones de entorno especiales.
2. En imágenes Docker minimalistas (Alpine o Distroless) exige instalar paquetes del sistema operativo (`libmagic-dev` / `file`), aumentando el tamaño final de la imagen y la superficie de ataque CVE.
3. El alcance del proyecto solo requiere distinguir 3 formatos de imagen bien especificados: JPEG, PNG y WebP.

## Decisión
Implementar un validador liviano en Python puro (`core/security.py`) o utilizar la biblioteca pura `filetype` sin dependencias de sistema C.

Las firmas binarias (magic bytes) a inspeccionar son:
- **JPEG:** Los primeros 3 bytes deben ser `\xFF\xD8\xFF`.
- **PNG:** Los primeros 8 bytes deben ser `\x89\x50\x4E\x47\x0D\x0A\x1A\x0A` (`\x89PNG\r\n\x1a\n`).
- **WebP:** Los primeros 4 bytes son `RIFF` (`\x52\x49\x46\x46`) y los bytes 8 al 12 son `WEBP` (`\x57\x45\x42\x50`).

Complementariamente, para asegurar la integridad estructural y descartar *decompression bombs*, la imagen se decodifica en un threadpool con `Pillow`, respetando `Image.MAX_IMAGE_PIXELS = 10_000_000`.

## Consecuencias
* **Positivas:**
  - Cero dependencias nativas en C / libmagic.
  - Portabilidad total e inmediata en Windows local, macOS y Linux contenedores sin paquetes del OS extra.
  - Ejecución ultrarrápida en memoria en O(1) leyendo los primeros 16 bytes del buffer.
* **Negativas / Mitigaciones:**
  - Solo reconoce los formatos soportados por la aplicación (JPEG, PNG, WebP). Para el alcance de AnimeFinder esto es exactamente lo deseado.
