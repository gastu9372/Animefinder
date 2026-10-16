from typing import Any

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """Esquema de error canónico según RFC 7807."""

    type: str = Field(default="about:blank", description="URI de referencia del tipo de error")
    title: str = Field(..., description="Título legible del error")
    status: int = Field(..., description="Código de estado HTTP")
    detail: str = Field(..., description="Descripción detallada del error para el cliente")
    instance: str | None = Field(default=None, description="URI del endpoint donde ocurrió el error")
    code: str = Field(..., description="Código de error interno del sistema")
    retry_after_seconds: int | None = Field(
        default=None, description="Segundos a esperar antes de reintentar si aplica"
    )


class AppException(Exception):
    """Excepción base para errores de negocio y dominio de la aplicación."""

    def __init__(
        self,
        status_code: int,
        code: str,
        title: str,
        detail: str,
        error_type: str = "about:blank",
        retry_after_seconds: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail
        self.error_type = error_type
        self.retry_after_seconds = retry_after_seconds
        self.extra = extra or {}


class InvalidImageError(AppException):
    def __init__(self, detail: str = "El archivo enviado no es una imagen válida o está corrupto.") -> None:
        super().__init__(
            status_code=400,
            code="INVALID_IMAGE",
            title="Invalid Image",
            detail=detail,
            error_type="https://animefinder.app/errors/invalid-image",
        )


class UnsupportedMediaTypeError(AppException):
    def __init__(
        self, detail: str = "Formato de imagen no soportado. Formatos admitidos: JPEG, PNG, WebP."
    ) -> None:
        super().__init__(
            status_code=415,
            code="UNSUPPORTED_MEDIA_TYPE",
            title="Unsupported Media Type",
            detail=detail,
            error_type="https://animefinder.app/errors/unsupported-media-type",
        )


class RateLimitExceededError(AppException):
    def __init__(
        self, detail: str = "Has superado el límite de peticiones permitido.", retry_after_seconds: int = 60
    ) -> None:
        super().__init__(
            status_code=429,
            code="RATE_LIMIT_EXCEEDED",
            title="Too Many Requests",
            detail=detail,
            error_type="https://animefinder.app/errors/rate-limit-exceeded",
            retry_after_seconds=retry_after_seconds,
        )


class QuotaDepletedError(AppException):
    def __init__(
        self,
        detail: str = "El cupo diario del motor de reconocimiento por imagen se ha agotado. Te invitamos a utilizar la búsqueda por descripción.",
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(
            status_code=402,
            code="IMAGE_QUOTA_DEPLETED",
            title="Search Quota Depleted",
            detail=detail,
            error_type="https://animefinder.app/errors/quota-depleted",
            retry_after_seconds=retry_after_seconds,
        )


class ExternalServiceUnavailableError(AppException):
    def __init__(
        self,
        service_name: str,
        detail: str = "El servicio externo se encuentra temporalmente degradado o no disponible.",
    ) -> None:
        super().__init__(
            status_code=503,
            code=f"{service_name.upper()}_UNAVAILABLE",
            title="External Service Unavailable",
            detail=detail,
            error_type="https://animefinder.app/errors/service-unavailable",
        )
