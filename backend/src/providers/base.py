from abc import ABC, abstractmethod

from src.domain.models import CanonicalAnime, RawImageMatch


class BaseImageSearchProvider(ABC):
    """Interfaz abstracta para motores de búsqueda inversa de anime por imagen."""

    @abstractmethod
    async def search_by_image(self, image_bytes: bytes) -> list[RawImageMatch]:
        """Envía el buffer binario de una imagen y devuelve coincidencias crudas de escenas."""
        pass

    @abstractmethod
    async def get_remaining_quota(self) -> int:
        """Consulta el cupo restante de búsquedas disponible."""
        pass


class BaseMetadataProvider(ABC):
    """Interfaz abstracta para proveedores de catálogo y metadatos de anime."""

    @abstractmethod
    async def get_anime_batch(self, anilist_ids: list[int]) -> dict[int, CanonicalAnime]:
        """Consulta en lote los metadatos de múltiples animes por su ID canónico."""
        pass

    @abstractmethod
    async def search_anime_by_title(self, query: str, limit: int = 5) -> list[CanonicalAnime]:
        """Búsqueda textual directa en el catálogo de animes."""
        pass
