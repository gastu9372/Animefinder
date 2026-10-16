import hashlib
import json
import logging
import time
from typing import Any

import nh3
from rapidfuzz import fuzz

from src.core.config import Settings, get_settings
from src.core.exceptions import RateLimitExceededError
from src.core.redis import get_redis_client
from src.domain.models import CanonicalAnime
from src.providers.anilist import AniListProvider
from src.providers.gemini_ai import (
    GeminiLLMProvider,
    LLMDailyCapReachedError,
    LLMNotConfiguredError,
)

logger = logging.getLogger(__name__)


def compute_title_similarity(candidate_title: str, anime: CanonicalAnime) -> float:
    """Calcula el ratio de similitud (0..1) entre el título propuesto y los títulos de AniList."""
    c_lower = candidate_title.lower().strip()
    ratios: list[float] = []

    if anime.title.romaji:
        ratios.append(fuzz.token_sort_ratio(c_lower, anime.title.romaji.lower().strip()) / 100.0)
    if anime.title.english:
        ratios.append(fuzz.token_sort_ratio(c_lower, anime.title.english.lower().strip()) / 100.0)

    return max(ratios) if ratios else 0.0


class TextSearchService:
    """Servicio coordinador para búsqueda de anime por descripción textual libre."""

    def __init__(
        self,
        settings: Settings | None = None,
        llm_provider: GeminiLLMProvider | None = None,
        anilist_provider: AniListProvider | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm_provider = llm_provider or GeminiLLMProvider(settings=self.settings)
        self.anilist_provider = anilist_provider or AniListProvider(settings=self.settings)

    async def check_rate_limits(self, client_ip: str) -> None:
        """Verifica rate limit por IP (10 req/min)."""
        try:
            redis = await get_redis_client()
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
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.warning("Fallo en Redis al verificar rate limits de texto", exc_info=e)

    async def search_by_description(
        self, raw_description: str, client_ip: str, limit: int = 5
    ) -> dict[str, Any]:
        start_time = time.perf_counter()

        # 1. Validar rate limit
        await self.check_rate_limits(client_ip)

        # 2. Normalización de entrada
        normalized_text = " ".join(raw_description.strip().split())[:500]
        text_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        cache_key = f"cache:text:{text_hash}"

        # 3. Comprobar caché en Redis
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
            logger.warning("Error leyendo caché de texto en Redis", exc_info=e)

        results: list[dict[str, Any]] = []
        filtered_count = 0
        search_mode = "llm"

        # 4. Intentar inferencia inteligente con LLM (Gemini)
        try:
            candidates = await self.llm_provider.infer_animes_from_description(
                normalized_text, limit=limit
            )

            # Cruzar candidatos contra AniList y validar similitud anti-alucinación
            for candidate in candidates:
                matches = await self.anilist_provider.search_anime_by_title(
                    candidate.anime_title, limit=1
                )
                if not matches:
                    filtered_count += 1
                    continue

                best_anime = matches[0]
                similarity_score = compute_title_similarity(candidate.anime_title, best_anime)

                # Si no supera el umbral estricto, descartar por posible alucinación
                if similarity_score < self.settings.TITLE_MATCH_MIN_SCORE:
                    logger.info(
                        "Candidato descartado por bajo puntaje de título",
                        extra={
                            "candidate": candidate.anime_title,
                            "match": best_anime.title.romaji,
                            "score": similarity_score,
                        },
                    )
                    filtered_count += 1
                    continue

                # Filtrar contenido adulto si está configurado
                if self.settings.ADULT_CONTENT_POLICY == "filter" and best_anime.is_adult:
                    filtered_count += 1
                    continue

                clean_reason = nh3.clean(candidate.match_reason, tags=set())

                results.append(
                    {
                        "id": best_anime.id,
                        "title": best_anime.title.model_dump(),
                        "cover_image": best_anime.cover_image,
                        "synopsis": best_anime.synopsis,
                        "year": best_anime.year,
                        "format": best_anime.format,
                        "is_adult": best_anime.is_adult,
                        "confidence_percentage": None,
                        "confidence_level": candidate.confidence_level,
                        "match_reason": clean_reason,
                        "scene_info": None,
                    }
                )

        except (LLMNotConfiguredError, LLMDailyCapReachedError, Exception) as exc:
            # Fallback automático elegante a búsqueda directa en AniList
            logger.info("Activando fallback automático a AniList: %s", str(exc))
            search_mode = "fallback"

            fallback_matches = await self.anilist_provider.search_anime_by_title(
                normalized_text, limit=limit
            )
            for anime in fallback_matches:
                if self.settings.ADULT_CONTENT_POLICY == "filter" and anime.is_adult:
                    filtered_count += 1
                    continue

                results.append(
                    {
                        "id": anime.id,
                        "title": anime.title.model_dump(),
                        "cover_image": anime.cover_image,
                        "synopsis": anime.synopsis,
                        "year": anime.year,
                        "format": anime.format,
                        "is_adult": anime.is_adult,
                        "confidence_percentage": None,
                        "confidence_level": "medium",
                        "match_reason": "Coincidencia por búsqueda textual directa en el catálogo de AniList.",
                        "scene_info": None,
                    }
                )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        response_payload = {
            "query_type": "text",
            "search_mode": search_mode,
            "cached": False,
            "filtered_count": filtered_count,
            "processing_time_ms": elapsed_ms,
            "results": results[:limit],
        }

        # 5. Guardar en Redis con TTL de 48 horas (172800 s)
        try:
            redis = await get_redis_client()
            await redis.setex(cache_key, 172800, json.dumps(response_payload))
        except Exception as e:
            logger.warning("Fallo al guardar resultado de texto en Redis", exc_info=e)

        return response_payload
