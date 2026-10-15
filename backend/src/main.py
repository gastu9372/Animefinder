import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.v1.router import api_v1_router
from src.core.config import get_settings
from src.core.exceptions import AppException, ProblemDetails
from src.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(debug=settings.DEBUG)
    logger.info("Iniciando servicio AnimeFinder Backend", extra={"environment": settings.ENVIRONMENT})
    yield
    logger.info("Deteniendo servicio AnimeFinder Backend")


def create_app() -> FastAPI:
    settings = get_settings()

    # Desactivar documentación interactiva en producción
    docs_url = None if settings.is_production else "/docs"
    redoc_url = None if settings.is_production else "/redoc"
    openapi_url = None if settings.is_production else "/openapi.json"

    app = FastAPI(
        title="AnimeFinder API",
        description="API Backend para reconocimiento de animes por imagen y descripción.",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # Configuración de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware de Errores RFC 7807
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        problem = ProblemDetails(
            type=exc.error_type,
            title=exc.title,
            status=exc.status_code,
            detail=exc.detail,
            instance=request.url.path,
            code=exc.code,
            retry_after_seconds=exc.retry_after_seconds,
        )
        headers = {}
        if exc.retry_after_seconds is not None:
            headers["Retry-After"] = str(exc.retry_after_seconds)
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(exclude_none=True),
            headers=headers,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        problem = ProblemDetails(
            type="about:blank",
            title="HTTP Error",
            status=exc.status_code,
            detail=str(exc.detail),
            instance=request.url.path,
            code="HTTP_ERROR",
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Excepción no controlada", exc_info=exc)
        problem = ProblemDetails(
            type="https://animefinder.app/errors/internal-server-error",
            title="Internal Server Error",
            status=500,
            detail="Ocurrió un error interno en el servidor. Por favor intente más tarde.",
            instance=request.url.path,
            code="INTERNAL_SERVER_ERROR",
        )
        return JSONResponse(
            status_code=500,
            content=problem.model_dump(exclude_none=True),
        )

    # Incluir rutas de API v1
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()
