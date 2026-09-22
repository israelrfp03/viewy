"""Orquesta una pregunta del asistente: interpreta (LLM), ejecuta (Python /
ORM / pandas), redacta (plantilla). El LLM nunca calcula ni redacta — solo
clasifica la pregunta en un intent y unos filtros ya acotados.
"""

from django.utils import timezone

from .handlers import INTENT_HANDLERS
from .llm import LLMError, parse_intent
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .responses import RESPONSE_RENDERERS

OUT_OF_SCOPE_MESSAGE = "Este asistente está pensado para responder preguntas sobre tu biblioteca de Viewy."
FALLBACK_MESSAGE = "No he podido interpretar tu pregunta ahora mismo. Inténtalo de nuevo en un momento."


def answer_question(user, question):
    """Devuelve (answer_text, error_code). error_code es None si todo fue bien."""
    question = question.strip()
    if not question:
        return "Escribe una pregunta sobre tu biblioteca.", None

    current_year = timezone.now().year

    try:
        filters = parse_intent(SYSTEM_PROMPT, build_user_prompt(question), current_year)
    except LLMError:
        return FALLBACK_MESSAGE, "llm_unavailable"

    intent = filters["intent"]

    if intent == "out_of_scope":
        return OUT_OF_SCOPE_MESSAGE, None

    if intent == "clarify":
        return filters["clarify_question"] or "¿Puedes darme un poco más de detalle sobre lo que quieres saber?", None

    handler = INTENT_HANDLERS.get(intent)
    if handler is None:
        return FALLBACK_MESSAGE, None

    result = handler(user, filters)
    return RESPONSE_RENDERERS[intent](result, filters), None
