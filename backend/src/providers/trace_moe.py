import asyncio
import logging
from typing import Any

import httpx

from src.core.config import Settings, get_settings
from src.core.exceptions import (
    ExternalServiceUnavailableError,
    InvalidImageError,
    QuotaDepletedError,
    RateLimitExceededError,
)
from src.domain.models import RawImageMatch
from src.providers.base import BaseImageSearchProvider

logger = logging.getLogger(__name__)


class TraceMoeProvider(BaseImageSearchProvider):
    """Adaptador concreto para la API de trace.moe.

    Implementa control de concurrencia = 1, deduplicación por anime,
    sincronización con /me y manejo explícito de códigos de estado.
    """

    def __init__(
        self, settings: Settings | None = None, http_client: httpx.AsyncClient | None = None
    ) -> None:
        self.settings = settings or get_settings()
        self._client = http_client
        self._semaphore = asyncio.Semaphore(self.settings.TRACEMOE_MAX_CONCURRENCY)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=15.0)

    async def get_remaining_quota(self) -> int:
        """Consulta el endpoint /me sin consumir cuota para conocer saldo restante."""
        client = await self._get_client()
        headers = {}
        if self.settings.TRACE_MOE_API_KEY:
            headers["x-trace-key"] = self.settings.TRACE_MOE_API_KEY

        try:
            resp = await client.get(f"{self.settings.TRACE_MOE_API_URL}/me", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                quota = data.get("quota", 100)
                used = data.get("quotaUsed", 0)
                remaining = max(0, quota - used)
                logger.info(
                    "trace.moe cuota sincronizada",
                    extra={"quota": quota, "used": used, "remaining": remaining},
                )
                return remaining
            return 0
        except Exception as e:
            logger.warning("Fallo al consultar /me de trace.moe", exc_info=e)
            return 0

    async def search_by_image(self, image_bytes: bytes) -> list[RawImageMatch]:
        """Envía la imagen binaria a trace.moe bajo semáforo de concurrencia."""
        async with self._semaphore:
            client = await self._get_client()
            headers = {"Content-Type": "image/jpeg"}
            if self.settings.TRACE_MOE_API_KEY:
                headers["x-trace-key"] = self.settings.TRACE_MOE_API_KEY

            url = f"{self.settings.TRACE_MOE_API_URL}/search"

            try:
                response = await client.post(url, content=image_bytes, headers=headers)
            except httpx.RequestError as exc:
                logger.error("Error de conexión con trace.moe", exc_info=exc)
                raise ExternalServiceUnavailableError(
                    "trace.moe", "Error al comunicarse con trace.moe"
                ) from exc

            # Procesamiento explícito de códigos HTTP
            if response.status_code == 400:
                raise InvalidImageError("trace.moe no pudo procesar la imagen enviada.")

            if response.status_code == 402:
                # Distinguir cuota vs concurrencia
                try:
                    err_json = response.json()
                    err_msg = str(err_json.get("error", "")).lower()
                except Exception:
                    err_msg = ""

                if "concurrency" in err_msg:
                    logger.warning(
                        "trace.moe reportó concurrencia excedida; reintentando brevemente..."
                    )
                    await asyncio.sleep(0.5)
                    response = await client.post(url, content=image_bytes, headers=headers)
                    if response.status_code == 402:
                        raise QuotaDepletedError("Límite de concurrencia de trace.moe persistente.")
                else:
                    raise QuotaDepletedError()

            if response.status_code == 429:
                raise RateLimitExceededError("Se ha superado el rate limit HTTP hacia trace.moe.")

            if response.status_code in {503, 504}:
                raise ExternalServiceUnavailableError(
                    "trace.moe",
                    "El motor de trace.moe se encuentra sobrecargado o en mantenimiento.",
                )

            if response.status_code != 200:
                raise ExternalServiceUnavailableError(
                    "trace.moe", f"Respuesta inesperada de trace.moe: HTTP {response.status_code}"
                )

            data = response.json()
            raw_results = data.get("result", [])
            return self._deduplicate_by_anime(raw_results)

    def _deduplicate_by_anime(self, results: list[dict[str, Any]]) -> list[RawImageMatch]:
        """Agrupa fotogramas devueltos por anilist_id y conserva solo el de mayor similitud."""
        best_matches: dict[int, RawImageMatch] = {}

        for item in results:
            anilist_id = item.get("anilist")
            if not anilist_id or not isinstance(anilist_id, int):
                continue

            similarity = float(item.get("similarity", 0.0))
            episode = item.get("episode")
            if isinstance(episode, (int, float)):
                ep_int = int(episode)
            else:
                ep_int = None

            match = RawImageMatch(
                anilist_id=anilist_id,
                similarity=similarity,
                episode=ep_int,
                from_seconds=float(item.get("from", 0.0)),
                to_seconds=float(item.get("to", 0.0)),
                video_url=item.get("video") if self.settings.ENABLE_VIDEO_PREVIEW else None,
            )

            # Si no existe o si la similitud actual es superior, guardarlo
            if anilist_id not in best_matches or similarity > best_matches[anilist_id].similarity:
                best_matches[anilist_id] = match

        # Ordenar descendentemente por nivel de similitud
        sorted_results = sorted(best_matches.values(), key=lambda m: m.similarity, reverse=True)
        return sorted_results
