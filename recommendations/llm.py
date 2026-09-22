"""Integración aislada con el proveedor de LLM (Gemini).

Si algún día cambiamos de proveedor, solo este archivo debería cambiar —
services.py y prompts.py no saben qué proveedor hay detrás. Mismo patrón que
integrations/tmdb.py y integrations/anilist.py.
"""

import json

import requests
from django.conf import settings

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODEL = "gemini-2.5-flash"  # más estable que gemini-3.6-flash en las pruebas de la Fase 11
REQUEST_TIMEOUT = 20

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


class LLMError(Exception):
    """Fallo genérico al comunicarse con el proveedor de LLM."""


class LLMTimeoutError(LLMError):
    pass


class LLMConfigError(LLMError):
    """API key ausente o mal configurada."""


class LLMResponseError(LLMError):
    """El proveedor respondió, pero el contenido no es JSON válido o utilizable."""


def get_recommendations_from_llm(system_prompt, user_prompt):
    """Llama al LLM y devuelve la lista de recomendaciones ya validada
    (máx. MAX_RECOMMENDATIONS, cada una con title/media_type/reason)."""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise LLMConfigError("Falta configurar GEMINI_API_KEY.")

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.6,
        },
    }

    try:
        response = requests.post(
            API_URL.format(model=MODEL),
            params={"key": api_key},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.Timeout as exc:
        raise LLMTimeoutError("El proveedor de recomendaciones no respondió a tiempo.") from exc
    except requests.exceptions.RequestException as exc:
        raise LLMError("No se pudo contactar con el proveedor de recomendaciones.") from exc

    if response.status_code == 429:
        raise LLMError("Límite de peticiones alcanzado. Inténtalo de nuevo en un momento.")
    if response.status_code != 200:
        raise LLMError(f"El proveedor respondió con un error inesperado ({response.status_code}).")

    try:
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMResponseError("La respuesta del proveedor no tiene el formato esperado.") from exc

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
