from fastapi import APIRouter

from src.api.v1.endpoints import health, search_image, search_text

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(search_image.router, tags=["Image Search"])
api_v1_router.include_router(search_text.router, tags=["Text Search"])
