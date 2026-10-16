import json
import logging
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from src.core.config import Settings, get_settings
from src.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(Exception):
    """Excepción cuando no se ha configurado la clave de Gemini."""
    pass


class LLMDailyCapReachedError(Exception):
    """Excepción cuando se supera el tope diario de llamadas al LLM."""
    pass


class LLMCandidate(BaseModel):
    anime_title: str = Field(..., description="Nombre representativo del anime (en romaji o inglés)")
    confidence_level: Literal["high", "medium", "low"] = Field(..., description="Nivel cualitativo de confianza")
    match_reason: str = Field(..., description="Breve justificación de por qué coincide con la descripción")


class LLMStructuredOutput(BaseModel):
    candidates: list[LLMCandidate] = Field(default_factory=list, description="Lista de hasta 5 animes candidatos")


class GeminiLLMProvider:
    """Adaptador para Google Gemini utilizando el SDK oficial google-genai y Structured Outputs."""

    SYSTEM_INSTRUCTION = """
    Eres un asistente experto en anime y manga ("otaku reasoning engine").
    El usuario te describirá escenas, personajes, tropos o tramas en lenguaje libre.
    Tu tarea es identificar los animes más probables que coincidan con la descripción.
    Reglas estrictas:
    1. Devuelve un máximo de 5 candidatos ordenados por probabilidad.
    2. El campo 'anime_title' debe ser el título canónico en romaji o inglés (por ejemplo: 'Death Note', 'Sousou no Frieren', 'Konosuba').
    3. Para 'confidence_level', asigna 'high', 'medium' o 'low'.
    4. Explica brevemente en 'match_reason' qué elementos de la descripción corresponden a la serie.
    5. Si la descripción es incoherente o no parece describir ningún anime, devuelve una lista vacía de candidatos.
    6. No inventes títulos de series inexistentes.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def infer_animes_from_description(self, description: str, limit: int = 5) -> list[LLMCandidate]:
        """Razona sobre la descripción y retorna candidatos estructurados."""
        if not self.settings.GEMINI_API_KEY:
            logger.info("GEMINI_API_KEY no configurada; activando fallback automático.")
            raise LLMNotConfiguredError("GEMINI_API_KEY no configurada.")

        # 1. Comprobar tope diario en Redis
        try:
            redis = await get_redis_client()
            daily_key = "quota:gemini:daily"
            current_calls = await redis.get(daily_key)
            if current_calls and int(current_calls) >= self.settings.LLM_DAILY_CALL_CAP:
                logger.warning("Tope diario de llamadas a Gemini alcanzado (%s)", self.settings.LLM_DAILY_CALL_CAP)
                raise LLMDailyCapReachedError("Tope diario alcanzado")
        except LLMDailyCapReachedError:
            raise
        except Exception as e:
            logger.warning("No se pudo verificar tope diario en Redis", exc_info=e)

        # 2. Invocación a Gemini SDK
        try:
            client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
            prompt = f"Descripción del usuario: \"{description}\"\nIdentifica los animes correspondientes (máximo {limit})."

            config = types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=LLMStructuredOutput,
                temperature=0.2,
            )

            # En el SDK google-genai generate_content es síncrono
            import asyncio
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.settings.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            # 3. Incrementar contador diario en Redis
            try:
                redis = await get_redis_client()
                count = await redis.incr(daily_key)
                if count == 1:
                    await redis.expire(daily_key, 86400)
            except Exception as e:
                logger.warning("No se pudo registrar llamada en Redis", exc_info=e)

            if not response.text:
                return []

            parsed = LLMStructuredOutput.model_validate_json(response.text)
            return parsed.candidates[:limit]
        except Exception as exc:
            logger.error("Error al invocar API de Google Gemini", exc_info=exc)
            raise
