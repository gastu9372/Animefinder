import json
import logging
import re
from typing import Any

import httpx
import nh3
from src.core.config import Settings, get_settings
from src.core.exceptions import ExternalServiceUnavailableError, RateLimitExceededError
from src.core.redis import get_redis_client
from src.domain.models import CanonicalAnime, TitleInfo
from src.providers.base import BaseMetadataProvider

logger = logging.getLogger(__name__)

# Regex para eliminar marcas de spoiler de AniList: ~!texto!~
SPOILER_REGEX = re.compile(r"~!.*?!(~|$)", flags=re.DOTALL)


def sanitize_synopsis(raw_description: str | None) -> str:
    """Elimina etiquetas HTML y marcas de spoiler de la sinopsis de AniList."""
    if not raw_description:
        return "Sinopsis no disponible."

    # 1. Eliminar marcas de spoiler ~! ... !~
    clean_text = SPOILER_REGEX.sub("[Contenido con spoiler omitido]", raw_description)

    # 2. Reemplazar saltos de línea HTML por saltos de línea reales
    clean_text = clean_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")

    # 3. Stripping total de etiquetas HTML residuales usando nh3 (Rust engine)
    clean_text = nh3.clean(clean_text, tags=set())

    return clean_text.strip()


class AniListProvider(BaseMetadataProvider):
    """Adaptador para AniList GraphQL v2 con soporte de Batching, Sanitización y Caché."""

    BATCH_QUERY = """
    query GetAnimeBatch($ids: [Int]) {
      Page(page: 1, perPage: 50) {
        media(id_in: $ids, type: ANIME) {
          id
          title {
            romaji
            english
            native
          }
          coverImage {
            extraLarge
            large
          }
          description(asHtml: false)
          seasonYear
          startDate {
            year
          }
          format
          isAdult
        }
      }
    }
    """

    SEARCH_QUERY = """
    query SearchAnime($search: String, $limit: Int) {
      Page(page: 1, perPage: $limit) {
        media(search: $search, type: ANIME) {
          id
          title {
            romaji
            english
            native
          }
          coverImage {
            extraLarge
            large
          }
          description(asHtml: false)
          seasonYear
          startDate {
            year
          }
          format
          isAdult
        }
      }
    }
    """

    def __init__(self, settings: Settings | None = None, http_client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=10.0)

    async def get_anime_batch(self, anilist_ids: list[int]) -> dict[int, CanonicalAnime]:
        """Consulta en UNA sola query GraphQL los metadatos de los IDs solicitados con caché en Redis."""
        if not anilist_ids:
            return {}

        results: dict[int, CanonicalAnime] = {}
        missing_ids: list[int] = []

        # 1. Intentar recuperar desde caché de Redis
        try:
            redis = await get_redis_client()
            for anime_id in anilist_ids:
                cached_json = await redis.get(f"anime:meta:{anime_id}")
                if cached_json:
                    results[anime_id] = CanonicalAnime.model_validate_json(cached_json)
                else:
                    missing_ids.append(anime_id)
        except Exception as e:
            logger.warning("Fallo al leer caché de Redis para AniList", exc_info=e)
            missing_ids = list(anilist_ids)

        if not missing_ids:
            return results

        # 2. Consultar AniList GraphQL en una sola petición para los IDs faltantes
        client = await self._get_client()
        payload = {
            "query": self.BATCH_QUERY,
            "variables": {"ids": missing_ids},
        }

        try:
            response = await client.post(self.settings.ANILIST_API_URL, json=payload)
        except httpx.RequestError as exc:
            logger.error("Error al contactar AniList GraphQL", exc_info=exc)
            raise ExternalServiceUnavailableError("AniList", "Fallo al consultar AniList") from exc

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning("AniList rate limit 429 alcanzado", extra={"retry_after": retry_after})
            raise RateLimitExceededError(
                "La API de AniList ha alcanzado su límite de peticiones.", retry_after_seconds=retry_after
            )

        if response.status_code != 200:
            raise ExternalServiceUnavailableError(
                "AniList", f"AniList respondió con estado HTTP {response.status_code}"
            )

        data = response.json()
        media_list = data.get("data", {}).get("Page", {}).get("media", [])

        for item in media_list:
            canonical = self._map_to_canonical(item)
            results[canonical.id] = canonical

            # Guardar en Redis con TTL de 48 horas (172800 s)
            try:
                redis = await get_redis_client()
                await redis.setex(f"anime:meta:{canonical.id}", 172800, canonical.model_dump_json())
            except Exception as e:
                logger.warning("Fallo al escribir en Redis", exc_info=e)

        return results

    async def search_anime_by_title(self, query: str, limit: int = 5) -> list[CanonicalAnime]:
        """Búsqueda textual directa en AniList GraphQL (utilizada como fallback)."""
        client = await self._get_client()
        payload = {
            "query": self.SEARCH_QUERY,
            "variables": {"search": query, "limit": limit},
        }

        try:
            response = await client.post(self.settings.ANILIST_API_URL, json=payload)
        except httpx.RequestError as exc:
            raise ExternalServiceUnavailableError("AniList", "Fallo de conexión a AniList") from exc

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitExceededError("AniList rate limit alcanzado.", retry_after_seconds=retry_after)

        if response.status_code != 200:
            raise ExternalServiceUnavailableError("AniList", f"Error AniList HTTP {response.status_code}")

        data = response.json()
        media_list = data.get("data", {}).get("Page", {}).get("media", [])
        return [self._map_to_canonical(item) for item in media_list]

    def _map_to_canonical(self, item: dict[str, Any]) -> CanonicalAnime:
        title_dict = item.get("title", {})
        title = TitleInfo(
            romaji=title_dict.get("romaji") or "Título desconocido",
            english=title_dict.get("english"),
            native=title_dict.get("native"),
        )

        cover_dict = item.get("coverImage", {})
        cover_url = (
            cover_dict.get("extraLarge")
            or cover_dict.get("large")
            or "https://via.placeholder.com/460x650?text=No+Cover"
        )

        year = item.get("seasonYear") or item.get("startDate", {}).get("year")
        synopsis = sanitize_synopsis(item.get("description"))

        return CanonicalAnime(
            id=item["id"],
            title=title,
            cover_image=cover_url,
            synopsis=synopsis,
            year=year,
            format=item.get("format"),
            is_adult=bool(item.get("isAdult", False)),
        )
