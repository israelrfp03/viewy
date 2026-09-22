"""Redacción determinista de la respuesta final: cada intent tiene su propia
plantilla en Python. Deliberadamente NO se usa una segunda llamada al LLM
aquí — todas las respuestas de este catálogo de intents son lo bastante
simples como para no necesitarla (ver Fase 12), y así nunca pueden alucinar.
"""

MEDIA_TYPE_LABELS_PLURAL = {"movie": "películas", "series": "series", "anime": "anime"}
MEDIA_TYPE_FEMININE = {"movie": True, "series": True, "anime": False}
STATUS_LABELS_PLURAL = {
    "planned": "pendientes",
    "watching": "viendo",
    "completed": "terminados",
    "dropped": "abandonados",
}
STATUS_LABELS_PLURAL_FEMININE = {
    "planned": "pendientes",
    "watching": "viendo",
    "completed": "terminadas",
    "dropped": "abandonadas",
}


def _status_label(status, feminine):
    labels = STATUS_LABELS_PLURAL_FEMININE if feminine else STATUS_LABELS_PLURAL
    return labels[status]
MONTH_NAMES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _type_scope(media_type, prefix=" de"):
    return f"{prefix} {MEDIA_TYPE_LABELS_PLURAL[media_type]}" if media_type else ""


def _period_phrase(year, month):
    if year and month:
        return f" en {MONTH_NAMES[month - 1]} de {year}"
    if year:
        return f" en {year}"
    if month:
        return f" en {MONTH_NAMES[month - 1]} (de cualquier año)"
    return ""


def render_total_library(result, filters):
    value = result["value"]
    if value == 0:
        return "Todavía no tienes ningún título en tu biblioteca."
    return f"Tienes {value} título{'s' if value != 1 else ''} en tu biblioteca."


def render_count_by_status(result, filters):
    if "value" in result:
        return f"Tienes {result['value']} título{'s' if result['value'] != 1 else ''} {STATUS_LABELS_PLURAL[result['status']]}."
    counts = result["counts"]
    parts = [f"{counts[s]} {STATUS_LABELS_PLURAL[s]}" for s in ("planned", "watching", "completed", "dropped")]
    return "Tu biblioteca por estado: " + ", ".join(parts) + "."


def render_count_by_type(result, filters):
    if "value" in result:
        return f"Tienes {result['value']} {MEDIA_TYPE_LABELS_PLURAL[result['media_type']]} ({result['percentage']}% de tu biblioteca)."
    breakdown = result["breakdown"]
    parts = [f"{data['count']} {MEDIA_TYPE_LABELS_PLURAL[value]}" for value, data in breakdown.items()]
    return "Por tipo de contenido: " + ", ".join(parts) + "."


def render_average_rating(result, filters):
    scope = _type_scope(result["media_type"])
    if result["average"] is None:
        return f"Todavía no tienes ninguna puntuación{scope} para calcular una nota media."
    return (
        f"Tu nota media{scope} es {result['average']}/10, "
        f"basada en {result['count']} título{'s' if result['count'] != 1 else ''} "
        f"puntuado{'s' if result['count'] != 1 else ''}."
    )


def render_top_rated(result, filters):
    items = result["items"]
    scope = _type_scope(result["media_type"], prefix="")
    feminine = MEDIA_TYPE_FEMININE.get(result["media_type"], False)
    suffix = "puntuadas" if feminine else "puntuados"
    if not items:
        return f"Todavía no tienes títulos{scope} {suffix}."
    lines = "\n".join(f"{i + 1}. {it['title']} — {it['rating']}/10" for i, it in enumerate(items))
    return f"Tus{scope} mejor {suffix}:\n{lines}"


def render_recently_completed(result, filters):
    items = result["items"]
    scope = _type_scope(result["media_type"], prefix="")
    if not items:
        return f"No has terminado nada{scope} todavía."
    lines = "\n".join(f"- {it['title']} ({it['finished_at']})" for it in items)
    return f"Lo último que has terminado{scope}:\n{lines}"


def render_completed_by_period(result, filters):
    value = result["value"]
    scope = _type_scope(result["media_type"])
    period = _period_phrase(result["year"], result["month"])
    return f"Terminaste {value} título{'s' if value != 1 else ''}{scope}{period}."


def render_most_active_month(result, filters):
    data = result["result"]
    if not data:
        return "Todavía no tienes suficiente actividad para saber cuál es tu mes más activo."
    return f"Tu mes más activo fue {data['month']}, con {data['count']} títulos terminados."


def render_favorites(result, filters):
    items = result["items"]
    scope = _type_scope(result["media_type"], prefix="")
    if not items:
        return f"Todavía no tienes favoritos{scope}."
    lines = "\n".join(f"- {it['title']}" for it in items)
    return f"Tus favoritos{scope}:\n{lines}"


def render_items_by_status(result, filters):
    items = result["items"]
    feminine = MEDIA_TYPE_FEMININE.get(result["media_type"], False)
    label = _status_label(result["status"], feminine)
    scope = _type_scope(result["media_type"], prefix="")
    if not items:
        return f"No tienes ningún título{scope} {label}."
    lines = "\n".join(f"- {it['title']}" for it in items)
    return f"Tus títulos{scope} {label}:\n{lines}"


def render_anime_stats(result, filters):
    data = result["result"]
    if not data:
        return (
            "Todavía no has enriquecido ningún anime con datos adicionales (estudio, origen...). "
            "Puedes hacerlo desde la ficha de un anime."
        )
    parts = []
    if data.get("top_studio"):
        parts.append(f"tu estudio de animación más frecuente es {data['top_studio']['studio']}")
    if data.get("top_source"):
        parts.append(f"tu origen más frecuente es {data['top_source']['source_material']}")
    if not parts:
        return "Todavía no tengo suficientes datos de estudio u origen de tus animes."
    frase = " y ".join(parts)
    return frase[0].upper() + frase[1:] + "."


def render_estimated_watch_time(result, filters):
    minutes = result["minutes"]
    if not minutes:
        return "Todavía no tengo suficientes películas con duración conocida para estimar tu tiempo visto."
    hours = round(minutes / 60, 1)
    return (
        f"Has visto aproximadamente {minutes} minutos (~{hours} horas) de películas "
        "— solo cuento películas con duración conocida, no series ni anime."
    )


def render_recommendation(result, filters):
    if result["error_code"] == "not_enough_data":
        return "Aún no tengo suficiente información sobre tus gustos para recomendarte algo. Añade y puntúa algunos títulos primero."
    if result["error_code"]:
        return "No he podido generar recomendaciones ahora mismo. Inténtalo de nuevo en un momento."
    titles = ", ".join(r["title"] for r in result["results"])
    return f"Te recomendaría: {titles}. Tienes el detalle completo en la página de Recomendaciones."


RESPONSE_RENDERERS = {
    "total_library": render_total_library,
    "count_by_status": render_count_by_status,
    "count_by_type": render_count_by_type,
    "average_rating": render_average_rating,
    "top_rated": render_top_rated,
    "recently_completed": render_recently_completed,
    "completed_by_period": render_completed_by_period,
    "most_active_month": render_most_active_month,
    "favorites": render_favorites,
    "items_by_status": render_items_by_status,
    "anime_stats": render_anime_stats,
    "estimated_watch_time": render_estimated_watch_time,
    "recommendation": render_recommendation,
}
