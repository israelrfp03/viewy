"""Integración con el proveedor de LLM para recomendaciones — envoltorio fino
sobre integrations/gemini.py (mecánica HTTP compartida) con la validación de
negocio específica de recomendaciones (forma, campos, límites).
"""

from integrations.gemini import (
    GeminiConfigError as LLMConfigError,
    GeminiError as LLMError,
    GeminiResponseError as LLMResponseError,
    GeminiTimeoutError as LLMTimeoutError,
    call_gemini,
)

VALID_MEDIA_TYPES = {"movie", "series", "anime"}
MAX_RECOMMENDATIONS = 5

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "recommendations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "media_type": {"type": "STRING", "enum": ["movie", "series", "anime"]},
                    "reason": {"type": "STRING"},
                },
                "required": ["title", "media_type", "reason"],
            },
        }
    },
    "required": ["recommendations"],
}


def get_recommendations_from_llm(system_prompt, user_prompt):
    """Llama al LLM y devuelve la lista de recomendaciones ya validada
    (máx. MAX_RECOMMENDATIONS, cada una con title/media_type/reason)."""
    parsed = call_gemini(system_prompt, user_prompt, RESPONSE_SCHEMA, temperature=0.6)
    return _validate_recommendations(parsed)


def _validate_recommendations(parsed):
    """Nunca confiamos ciegamente en la salida del LLM, ni siquiera con
    structured output: revalidamos estructura, tipos y límites nosotros."""
    if not isinstance(parsed, dict):
        raise LLMResponseError("La respuesta del proveedor no es un objeto JSON.")

    raw_items = parsed.get("recommendations")
    if not isinstance(raw_items, list):
        raise LLMResponseError("La respuesta no incluye una lista de recomendaciones.")

    valid = []
    for item in raw_items[: MAX_RECOMMENDATIONS * 2]:  # margen antes de recortar de verdad
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        media_type = item.get("media_type")
        reason = item.get("reason")
        if not isinstance(title, str) or not title.strip():
            continue
        if media_type not in VALID_MEDIA_TYPES:
            continue
        if not isinstance(reason, str) or not reason.strip():
            continue
        valid.append({"title": title.strip(), "media_type": media_type, "reason": reason.strip()})
        if len(valid) == MAX_RECOMMENDATIONS:
            break

    return valid
