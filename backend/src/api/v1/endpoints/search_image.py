import logging
from typing import Any

from fastapi import APIRouter, File, Request, UploadFile
from src.core.config import get_settings
from src.core.exceptions import InvalidImageError, UnsupportedMediaTypeError
from src.core.security import is_allowed_image
from src.services.image_search_service import ImageSearchService

router = APIRouter()
logger = logging.getLogger(__name__)

_image_service: ImageSearchService | None = None


def get_image_service() -> ImageSearchService:
    global _image_service
    if _image_service is None:
        _image_service = ImageSearchService()
    return _image_service


def extract_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente confiando en X-Forwarded-For solo si proviene de proxies conocidos."""
    settings = get_settings()
    client_host = request.client.host if request.client else "127.0.0.1"

    # Verificar si el socket directo proviene de un proxy confiable
    is_trusted = any(
        client_host == trusted or client_host.startswith(trusted.replace("/12", "").replace("/8", ""))
        for trusted in settings.trusted_proxies_list
    )

    if is_trusted:
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Tomar la primera IP de la lista
            real_ip = x_forwarded_for.split(",")[0].strip()
            if real_ip:
                return real_ip
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip.strip()

    return client_host


@router.post("/search/image", summary="Búsqueda inversa de anime por imagen")
async def search_by_image(
    request: Request,
    file: UploadFile = File(..., description="Archivo de imagen (JPEG, PNG, WebP) hasta 8MB"),
) -> dict[str, Any]:
    settings = get_settings()
    client_ip = extract_client_ip(request)

    # 1. Leer buffer y validar tamaño máximo
    content = await file.read()
    if len(content) == 0:
        raise InvalidImageError("El archivo de imagen está vacío.")

    if len(content) > settings.MAX_IMAGE_SIZE_BYTES:
        raise InvalidImageError(f"La imagen supera el tamaño máximo permitido de {settings.MAX_IMAGE_SIZE_BYTES // (1024*1024)} MB.")

    # 2. Validación de Magic Bytes en Python puro (ADR 0001)
    if not is_allowed_image(content):
        raise UnsupportedMediaTypeError("Formato no admitido. Formatos permitidos: JPEG, PNG, WebP.")

    # 3. Invocar servicio
    service = get_image_service()
    return await service.search_by_image(content, client_ip)
