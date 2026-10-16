"""Módulo de seguridad para validación de magic bytes e integridad de imágenes en Python puro.

Conforme a la decisión de arquitectura ADR 0001, se inspeccionan las firmas binarias
nativas sin dependencias del binario C libmagic.
"""

from typing import Literal

ImageType = Literal["jpeg", "png", "webp"]

# Firmas binarias estándar (Magic Bytes)
JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RIFF_SIGNATURE = b"RIFF"
WEBP_SIGNATURE = b"WEBP"


def detect_image_type(buffer: bytes) -> ImageType | None:
    """Detecta el tipo de imagen mediante la inspección de los magic bytes iniciales."""
    if len(buffer) < 12:
        return None

    # JPEG comienza con FF D8 FF
    if buffer.startswith(JPEG_SIGNATURE):
        return "jpeg"

    # PNG comienza con 89 50 4E 47 0D 0A 1A 0A
    if buffer.startswith(PNG_SIGNATURE):
        return "png"

    # WebP: Comienza con 'RIFF' en bytes 0..3 y tiene 'WEBP' en bytes 8..11
    if buffer.startswith(RIFF_SIGNATURE) and buffer[8:12] == WEBP_SIGNATURE:
        return "webp"

    return None


def is_allowed_image(buffer: bytes) -> bool:
    """Verifica si el buffer corresponde a un formato de imagen permitido (JPEG, PNG o WebP)."""
    return detect_image_type(buffer) is not None
