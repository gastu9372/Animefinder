from typing import Literal

from pydantic import BaseModel, Field


class TitleInfo(BaseModel):
    romaji: str = Field(..., description="Título en alfabeto latino (romaji)")
    english: str | None = Field(default=None, description="Título oficial en inglés si existe")
    native: str | None = Field(default=None, description="Título original en japonés/kanji")


class SceneInfo(BaseModel):
    episode: int | None = Field(default=None, description="Número de episodio detectado")
    timestamp_seconds: float | None = Field(default=None, description="Segundo exacto de la escena")
    timestamp_formatted: str | None = Field(default=None, description="Timestamp legible (MM:SS)")
    preview_video_url: str | None = Field(default=None, description="URL temporal de vista previa")


class RawImageMatch(BaseModel):
    anilist_id: int = Field(..., description="ID canónico de AniList")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Nivel de similitud decimal (0..1)")
    episode: int | None = None
    from_seconds: float = 0.0
    to_seconds: float = 0.0
    video_url: str | None = None


class CanonicalAnime(BaseModel):
    id: int = Field(..., description="ID canónico en AniList")
    title: TitleInfo
    cover_image: str = Field(..., description="URL de la portada en alta resolución")
    synopsis: str = Field(..., description="Sinopsis limpia de la obra")
    year: int | None = Field(default=None, description="Año de estreno")
    format: str | None = Field(default=None, description="Formato (TV, MOVIE, OVA, etc.)")
    is_adult: bool = Field(default=False, description="Indica si es contenido para adultos (+18)")


class SearchResultItem(BaseModel):
    id: int
    title: TitleInfo
    cover_image: str
    synopsis: str
    year: int | None = None
    format: str | None = None
    is_adult: bool = False
    confidence_percentage: float | None = None
    confidence_level: Literal["high", "medium", "low"]
    match_reason: str | None = None
    scene_info: SceneInfo | None = None
