import logging
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from src.api.v1.endpoints.search_image import extract_client_ip
from src.services.text_search_service import TextSearchService

router = APIRouter()
logger = logging.getLogger(__name__)

_text_service: TextSearchService | None = None


def get_text_service() -> TextSearchService:
    global _text_service
    if _text_service is None:
        _text_service = TextSearchService()
    return _text_service


class TextSearchRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Descripción libre de trama, personajes o escenas",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Número máximo de resultados a retornar (1-10)",
    )


@router.post("/search/text", summary="Búsqueda de anime por descripción textual libre")
async def search_by_text(
    request: Request,
    payload: TextSearchRequest,
) -> dict[str, Any]:
    client_ip = extract_client_ip(request)
    service = get_text_service()
    return await service.search_by_description(
        raw_description=payload.description,
        client_ip=client_ip,
        limit=payload.limit,
    )
