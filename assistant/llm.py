"""Clasificación de intents vía Gemini + validación defensiva.

El LLM devuelve intent+filtros; este módulo nunca confía ciegamente en esa
salida (ni siquiera viniendo ya validada por el schema de la API) — revalida
cada campo contra listas cerradas y rangos razonables antes de que llegue al
router. Esta es la barrera de seguridad real, no el prompt.
"""

from integrations.gemini import (
    GeminiConfigError as LLMConfigError,
    GeminiError as LLMError,
    GeminiResponseError as LLMResponseError,
    GeminiTimeoutError as LLMTimeoutError,
    call_gemini,
)

VALID_INTENTS = {
    "total_library",
    "count_by_status",
    "count_by_type",
    "average_rating",
    "top_rated",
    "recently_completed",
    "completed_by_period",
    "most_active_month",
    "favorites",
    "items_by_status",
    "anime_stats",
    "estimated_watch_time",
    "recommendation",
    "clarify",
    "out_of_scope",
}
VALID_MEDIA_TYPES = {"movie", "series", "anime"}
VALID_STATUSES = {"planned", "watching", "completed", "dropped"}
MIN_YEAR = 1900
MAX_LIMIT = 10
DEFAULT_LIMIT = 5

INTENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "intent": {"type": "STRING", "enum": sorted(VALID_INTENTS)},
        "media_type": {"type": "STRING", "enum": sorted(VALID_MEDIA_TYPES), "nullable": True},
        "status": {"type": "STRING", "enum": sorted(VALID_STATUSES), "nullable": True},
        "year": {"type": "INTEGER", "nullable": True},
        "month": {"type": "INTEGER", "nullable": True},
        "limit": {"type": "INTEGER", "nullable": True},
        "clarify_question": {"type": "STRING", "nullable": True},
        "recommendation_text": {"type": "STRING", "nullable": True},
    },
    "required": ["intent"],
}


def parse_intent(system_prompt, user_prompt, current_year):
    """Llama al LLM y devuelve un dict de intent ya validado y saneado:
    {"intent": ..., "media_type": ..., "status": ..., "year": ..., "month": ...,
     "limit": ..., "clarify_question": ..., "recommendation_text": ...}

    Cualquier campo inválido se sanea a None en vez de propagar el dato tal
    cual — el router nunca ve un valor fuera de lo permitido."""
    parsed = call_gemini(system_prompt, user_prompt, INTENT_SCHEMA, temperature=0.1)
    return _validate_intent(parsed, current_year)


def _validate_intent(parsed, current_year):
    if not isinstance(parsed, dict):
        raise LLMResponseError("La respuesta del proveedor no es un objeto JSON.")

    intent = parsed.get("intent")
    if intent not in VALID_INTENTS:
        raise LLMResponseError(f"Intent no reconocido: {intent!r}.")

    media_type = parsed.get("media_type")
    if media_type not in VALID_MEDIA_TYPES:
        media_type = None

    status = parsed.get("status")
    if status not in VALID_STATUSES:
        status = None

    year = parsed.get("year")
    if not isinstance(year, int) or not (MIN_YEAR <= year <= current_year + 1):
        year = None

    month = parsed.get("month")
    if not isinstance(month, int) or not (1 <= month <= 12):
        month = None

    limit = parsed.get("limit")
    if not isinstance(limit, int) or limit <= 0:
        limit = DEFAULT_LIMIT
    limit = min(limit, MAX_LIMIT)

    clarify_question = parsed.get("clarify_question")
    if not isinstance(clarify_question, str) or not clarify_question.strip():
        clarify_question = None

    recommendation_text = parsed.get("recommendation_text")
    if not isinstance(recommendation_text, str):
        recommendation_text = ""

    return {
        "intent": intent,
        "media_type": media_type,
        "status": status,
        "year": year,
        "month": month,
        "limit": limit,
        "clarify_question": clarify_question,
        "recommendation_text": recommendation_text.strip(),
    }
