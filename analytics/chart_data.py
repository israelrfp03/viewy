"""Reformatea `stats` (ya calculado por services.py/dataframes.py) a la forma
que espera Chart.js. No hace ninguna consulta ni ningún cálculo nuevo — solo
reshaping puro sobre datos que ya existen en memoria.

Cada clave del resultado es `None` cuando no hay datos suficientes para esa
gráfica, para que la plantilla pueda mostrar un mensaje en vez de un canvas
vacío.
"""

MEDIA_TYPE_LABELS = {"movie": "Película", "series": "Serie", "anime": "Anime"}


def build_chart_data(stats):
    return {
        "monthly_activity": _monthly_activity(stats),
        "type_breakdown": _type_breakdown(stats),
        "rating_distribution": _rating_distribution(stats),
        "ratings_by_type": _ratings_by_type(stats),
        "yearly_activity": _yearly_activity(stats),
        "type_over_time": _type_over_time(stats),
    }


def _monthly_activity(stats):
    rows = stats["advanced"]["monthly_completions"]
    if not rows:
        return None
    return {
        "labels": [row["month"] for row in rows],
        "data": [row["count"] for row in rows],
    }


def _type_breakdown(stats):
    breakdown = stats["media_type_breakdown"]
    rows = [(value, data) for value, data in breakdown.items() if data["count"] > 0]
    if not rows:
        return None
    return {
        "labels": [data["label"] for _, data in rows],
        "data": [data["count"] for _, data in rows],
    }


def _rating_distribution(stats):
    rows = stats["advanced"]["rating_distribution"]
    if not rows:
        return None
    return {
        "labels": [str(row["rating"]) for row in rows],
        "data": [row["count"] for row in rows],
    }


def _ratings_by_type(stats):
    rows = stats["advanced"]["ratings_by_type"]
    if not rows:
        return None
    return {
        "labels": [MEDIA_TYPE_LABELS.get(row["media_type"], row["media_type"]) for row in rows],
        "data": [row["average"] for row in rows],
    }


def _yearly_activity(stats):
    rows = stats["advanced"]["yearly_activity"]
    if not rows:
        return None
    return {
        "labels": [str(row["year"]) for row in rows],
        "data": [row["count"] for row in rows],
    }


def _type_over_time(stats):
    rows = stats["advanced"]["content_type_over_time"]
    if not rows:
        return None
    return {
        "labels": [row["month"] for row in rows],
        "datasets": {
            "movie": [row["movie"] for row in rows],
            "series": [row["series"] for row in rows],
            "anime": [row["anime"] for row in rows],
        },
    }
