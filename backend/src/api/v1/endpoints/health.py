from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Estado del servicio")
    timestamp: str = Field(..., description="Timestamp ISO-8601 UTC actual")
    version: str = Field(default="0.1.0", description="Versión del servicio")


@router.get("/health", response_model=HealthResponse, summary="Verificación de salud del servicio")
async def health_check() -> HealthResponse:
    """Endpoint mínimo de liveness/readiness probe."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version="0.1.0",
    )
