"""Parser determinista de líneas "título [rating]". Intenta resolver el caso
simple con regex, sin gastar ninguna llamada a un LLM. Solo marca una línea
como "confianza baja" cuando de verdad hay ambigüedad real (dígitos presentes
pero en una forma que no reconocemos con seguridad) — esas se agrupan y se
mandan una única vez al parser LLM (ver imports/llm.py), nunca una por línea.
"""

import re
from dataclasses import dataclass

# título (no codicioso) + separadores opcionales + rating (1-2 dígitos, decimal
# opcional con "." o ",") + paréntesis/"/10" opcionales + fin de línea.
RATING_PATTERN = re.compile(
    r"^(?P<title>.*?)"
    r"[\s\-:|⭐]*"
    r"\(?"
    r"(?P<rating>\d{1,2}(?:[.,]\d)?)"
    r"\)?"
    r"(?:\s*/\s*10)?"
    r"\s*$"
)

TITLE_STRIP_CHARS = " -:|()⭐"


@dataclass
class ParsedLine:
    raw_text: str
    title: str
    rating: float | None
    confidence: str  # "high" | "low"


def parse_line(raw_text):
    text = raw_text.strip()
    if not text:
        return None

    match = RATING_PATTERN.match(text)
    if match:
        title = match.group("title").strip(TITLE_STRIP_CHARS)
        # Si el "título" que queda tras extraer el rating está vacío o es
        # puramente numérico, probablemente ese número ERA el título completo
        # (ej. "1917") y no hay ningún rating real — no confiamos en el match.
        if title and not title.replace(" ", "").isdigit():
            rating = float(match.group("rating").replace(",", "."))
            return ParsedLine(raw_text=text, title=title, rating=rating, confidence="high")
        return ParsedLine(raw_text=text, title=text, rating=None, confidence="low")

    if any(ch.isdigit() for ch in text):
        # Hay dígitos pero no encajan en ningún patrón reconocido con seguridad.
        return ParsedLine(raw_text=text, title=text, rating=None, confidence="low")

    return ParsedLine(raw_text=text, title=text, rating=None, confidence="high")


def parse_text(text):
    """Devuelve una lista de ParsedLine, una por línea no vacía."""
    parsed = []
    for raw_line in text.splitlines():
        result = parse_line(raw_line)
        if result is not None:
            parsed.append(result)
    return parsed
