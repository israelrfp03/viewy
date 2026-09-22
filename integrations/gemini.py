"""Cliente genérico para la API de Gemini — mismo patrón que tmdb.py/anilist.py.

Solo se encarga de la mecánica HTTP (petición, timeout, parseo del JSON de
texto que devuelve el modelo). No sabe nada del significado de los datos:
eso es responsabilidad de quien lo llama (recommendations/llm.py,
assistant/llm.py...), que define su propio response_schema y valida el
resultado según su propio dominio.
"""

import json

import requests
from django.conf import settings

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash"  # ver Fase 11: más estable que gemini-3.6-flash en las pruebas
DEFAULT_TIMEOUT = 20


class GeminiError(Exception):
    """Fallo genérico al comunicarse con Gemini."""


class GeminiTimeoutError(GeminiError):
    pass


class GeminiConfigError(GeminiError):
    """API key ausente o mal configurada."""


class GeminiResponseError(GeminiError):
    """Gemini respondió, pero el contenido no es JSON válido o utilizable."""


def call_gemini(system_prompt, user_prompt, response_schema, temperature=0.6, model=None, timeout=None):
    """Llama a Gemini con structured output y devuelve el dict ya parseado.

    No valida el *contenido* del dict contra ninguna regla de negocio — solo
    garantiza que la respuesta es JSON válido con la forma que pidió el
    schema a nivel de API. La validación de negocio es cosa de cada llamador.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise GeminiConfigError("Falta configurar GEMINI_API_KEY.")

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
            "temperature": temperature,
        },
    }

    try:
        response = requests.post(
            API_URL.format(model=model or DEFAULT_MODEL),
            params={"key": api_key},
            json=payload,
            timeout=timeout or DEFAULT_TIMEOUT,
        )
    except requests.exceptions.Timeout as exc:
        raise GeminiTimeoutError("Gemini no respondió a tiempo.") from exc
    except requests.exceptions.RequestException as exc:
        raise GeminiError("No se pudo contactar con Gemini.") from exc

    if response.status_code == 429:
        raise GeminiError("Límite de peticiones alcanzado. Inténtalo de nuevo en un momento.")
    if response.status_code != 200:
        raise GeminiError(f"Gemini respondió con un error inesperado ({response.status_code}).")

    try:
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)
    except (KeyError, IndexError, ValueError) as exc:
        raise GeminiResponseError("La respuesta de Gemini no tiene el formato esperado.") from exc
