import asyncio
import hashlib
import io
import json
import logging
import time
from typing import Any

from PIL import Image

from src.core.config import Settings, get_settings
from src.core.exceptions import InvalidImageError, RateLimitExceededError
from src.core.redis import get_redis_client
from src.providers.anilist import AniListProvider
from src.providers.trace_moe import TraceMoeProvider

logger = logging.getLogger(__name__)

# Prevenir ataques de bomba de descompresión (Pixel Flood)
Image.MAX_IMAGE_PIXELS = 10_000_000


def _process_image_sync(raw_bytes: bytes) -> bytes:
    """Procesamiento síncrono intensivo en CPU: decodificación, resize y strip de EXIF."""
    try:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            # Convertir imágenes RGBA/paleta a RGB para compresión JPEG estándar
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Reescalado proporcional si excede 1280x720
            max_w, max_h = 1280, 720
            if img.width > max_w or img.height > max_h:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            # Guardar sin metadatos EXIF en calidad 85 optimizada
            img.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()
    except Exception as exc:
        raise InvalidImageError("No fue posible decodificar o sanitizar la imagen.") from exc


def format_timestamp(seconds: float | None) -> str | None:
    if seconds is None or seconds < 0:
        return None
    total_seconds = int(seconds)
    mins = total_seconds // 60
    secs = total_seconds % 60
    return f"{mins:02d}:{secs:02d}"


class ImageSearchService:
    """Servicio coordinador para búsqueda inversa de anime por imagen."""

    def __init__(
        self,
        settings: Settings | None = None,
        trace_provider: TraceMoeProvider | None = None,
        anilist_provider: AniListProvider | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.trace_provider = trace_provider or TraceMoeProvider(settings=self.settings)
        self.anilist_provider = anilist_provider or AniListProvider(settings=self.settings)
        self._mem_semaphore = asyncio.Semaphore(self.settings.IMAGE_PROCESSING_CONCURRENCY)

    async def check_rate_limits(self, client_ip: str) -> None:
        """Verifica los límites de peticiones por minuto y por día para la IP del cliente."""
        try:
            redis = await get_redis_client()

            # 1. Límite por minuto
            min_key = f"ratelimit:ip:{client_ip}:min"
            req_count = await redis.incr(min_key)
            if req_count == 1:
                await redis.expire(min_key, 60)
            if req_count > self.settings.RATE_LIMIT_PER_IP_PER_MIN:
                ttl = await redis.ttl(min_key)
                raise RateLimitExceededError(
                    detail="Has superado el límite de 10 peticiones por minuto.",
                    retry_after_seconds=max(1, ttl),
                )

            # 2. Límite diario de búsqueda de imágenes
            day_key = f"ratelimit:ip:{client_ip}:image:day"
            day_count = await redis.incr(day_key)
            if day_count == 1:
                await redis.expire(day_key, 86400)
            if day_count > self.settings.IMAGE_SEARCH_PER_IP_PER_DAY:
                ttl = await redis.ttl(day_key)
                raise RateLimitExceededError(
                    detail="Has alcanzado el límite diario de 10 búsquedas por imagen. Te invitamos a buscar por descripción.",
                    retry_after_seconds=max(1, ttl),
                )
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.warning("Fallo en Redis al verificar rate limits por IP", exc_info=e)

    async def search_by_image(self, raw_bytes: bytes, client_ip: str) -> dict[str, Any]:
        start_time = time.perf_counter()

        # 1. Validar rate limits en Redis
        await self.check_rate_limits(client_ip)

        # 2. Sanitizar imagen en threadpool bajo semáforo de memoria
        async with self._mem_semaphore:
            processed_bytes = await asyncio.to_thread(_process_image_sync, raw_bytes)

        # 3. Hash SHA-256 exacto
        image_hash = hashlib.sha256(processed_bytes).hexdigest()
        cache_key = f"cache:image:{image_hash}"

        # 4. Verificar caché en Redis
        try:
            redis = await get_redis_client()
            cached_payload = await redis.get(cache_key)
            if cached_payload:
                cached_data = json.loads(cached_payload)
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                cached_data["cached"] = True
                cached_data["processing_time_ms"] = elapsed_ms
                return cached_data
        except Exception as e:
            logger.warning("Error leyendo caché de imagen en Redis", exc_info=e)

        # 5. Consultar a trace.moe
        raw_matches = await self.trace_provider.search_by_image(processed_bytes)

        if not raw_matches:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "query_type": "image",
                "search_mode": "trace.moe",
                "cached": False,
                "filtered_count": 0,
                "processing_time_ms": elapsed_ms,
                "results": [],
            }

        # 6. Consultar metadatos en batch con AniList
        anilist_ids = [m.anilist_id for m in raw_matches]
        canonical_map = await self.anilist_provider.get_anime_batch(anilist_ids)

        # 7. Construir resultados y aplicar filtro de contenido adulto
        results: list[dict[str, Any]] = []
        filtered_count = 0

        for match in raw_matches:
            anime_meta = canonical_map.get(match.anilist_id)
            if not anime_meta:
                continue

            # Filtrado de contenido adulto según política
            if self.settings.ADULT_CONTENT_POLICY == "filter" and anime_meta.is_adult:
                filtered_count += 1
                continue

            # Cálculo de confianza
            confidence_pct = round(match.similarity * 100, 1)
            if match.similarity >= self.settings.SIMILARITY_THRESHOLD_HIGH:
                confidence_level = "high"
            elif match.similarity >= self.settings.SIMILARITY_THRESHOLD_LOW:
                confidence_level = "medium"
            else:
                confidence_level = "low"

            scene_info = {
                "episode": match.episode,
                "timestamp_seconds": match.from_seconds,
                "timestamp_formatted": format_timestamp(match.from_seconds),
                "preview_video_url": match.video_url,
            }

            result_item = {
                "id": anime_meta.id,
                "title": anime_meta.title.model_dump(),
                "cover_image": anime_meta.cover_image,
                "synopsis": anime_meta.synopsis,
                "year": anime_meta.year,
                "format": anime_meta.format,
                "is_adult": anime_meta.is_adult,
                "confidence_percentage": confidence_pct,
                "confidence_level": confidence_level,
                "match_reason": None,
                "scene_info": scene_info,
            }
            results.append(result_item)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        response_payload = {
            "query_type": "image",
            "search_mode": "trace.moe",
            "cached": False,
            "filtered_count": filtered_count,
            "processing_time_ms": elapsed_ms,
            "results": results,
        }

        # 8. Guardar en caché en Redis (TTL 72h) excluyendo preview_video_url que expira en 300s
        try:
            cache_copy = dict(response_payload)
            cache_results = []
            for item in results:
                item_copy = dict(item)
                if item_copy.get("scene_info"):
                    s_copy = dict(item_copy["scene_info"])
                    s_copy["preview_video_url"] = None  # No cachear enlace temporal de video
                    item_copy["scene_info"] = s_copy
                cache_results.append(item_copy)
            cache_copy["results"] = cache_results

            redis = await get_redis_client()
            await redis.setex(cache_key, 259200, json.dumps(cache_copy))
        except Exception as e:
            logger.warning("Fallo al escribir resultado de imagen en Redis", exc_info=e)

        return response_payload
