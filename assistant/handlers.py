"""Router de intents: un diccionario intent -> función, nada de encadenar
if/elif. Cada función recibe (user, filters) ya validados por assistant/llm.py
y devuelve un resultado estructurado — nunca texto. El LLM nunca ejecuta
código: esto es Python puro sobre ORM/pandas ya existentes.

"clarify" y "out_of_scope" no están en el router: no ejecutan nada, se
gestionan antes de llegar aquí (assistant/services.py).
"""

from analytics.dataframes import (
    busiest_month,
    content_type_over_time,
    get_library_dataframe,
    monthly_completions,
    ratings_by_type,
    yearly_activity,
)
from analytics.services import (
    anime_stats as get_anime_stats,
    get_favorites,
    get_top_rated,
    media_type_breakdown,
    movie_watch_time,
    rating_stats,
    recent_completed,
    status_counts,
)
from library.models import UserMedia
from recommendations.services import get_recommendations


def _serialize_entries(entries, show_date=False):
    items = []
    for entry in entries:
        item = {"title": entry.media.title, "media_type": entry.media.media_type, "rating": entry.rating}
        if show_date:
            item["finished_at"] = entry.finished_at
        items.append(item)
    return items


def handle_total_library(user, filters):
    return {"value": UserMedia.objects.filter(user=user).count()}


def handle_count_by_status(user, filters):
    queryset = UserMedia.objects.filter(user=user)
    counts = status_counts(queryset)
    if filters["status"]:
        return {"value": counts[filters["status"]], "status": filters["status"]}
    return {"counts": counts}


def handle_count_by_type(user, filters):
    queryset = UserMedia.objects.filter(user=user)
    breakdown = media_type_breakdown(queryset, queryset.count())
    if filters["media_type"]:
        data = breakdown[filters["media_type"]]
        return {"value": data["count"], "media_type": filters["media_type"], "percentage": data["percentage"]}
    return {"breakdown": breakdown}


def handle_average_rating(user, filters):
    if filters["media_type"]:
        df = get_library_dataframe(user)
        match = next((r for r in ratings_by_type(df) if r["media_type"] == filters["media_type"]), None)
        if not match:
            return {"average": None, "count": 0, "media_type": filters["media_type"]}
        return {"average": match["average"], "count": match["count"], "media_type": filters["media_type"]}

    stats = rating_stats(UserMedia.objects.filter(user=user))
    return {"average": stats["average"], "count": stats["rated_count"], "media_type": None}


def handle_top_rated(user, filters):
    entries = get_top_rated(user, media_type=filters["media_type"], limit=filters["limit"])
    return {"items": _serialize_entries(entries), "media_type": filters["media_type"]}


def handle_recently_completed(user, filters):
    queryset = UserMedia.objects.filter(user=user)
    entries = recent_completed(queryset, media_type=filters["media_type"], limit=filters["limit"])
    return {"items": _serialize_entries(entries, show_date=True), "media_type": filters["media_type"]}


def handle_completed_by_period(user, filters):
    df = get_library_dataframe(user)
    year, month, media_type = filters["year"], filters["month"], filters["media_type"]

    if media_type:
        value = 0
        for row in content_type_over_time(df):
            row_year, row_month = (int(part) for part in row["month"].split("-"))
            if year and row_year != year:
                continue
            if month and row_month != month:
                continue
            value += row.get(media_type, 0)
    elif year and month:
        target = f"{year:04d}-{month:02d}"
        value = next((r["count"] for r in monthly_completions(df) if r["month"] == target), 0)
    elif year:
        value = next((r["count"] for r in yearly_activity(df) if r["year"] == year), 0)
    else:
        value = int(df["finished_at"].notna().sum()) if not df.empty else 0

    return {"value": value, "media_type": media_type, "year": year, "month": month}


def handle_most_active_month(user, filters):
    return {"result": busiest_month(get_library_dataframe(user))}


def handle_favorites(user, filters):
    entries = get_favorites(user, media_type=filters["media_type"], limit=filters["limit"])
    return {"items": _serialize_entries(entries), "media_type": filters["media_type"]}


def handle_items_by_status(user, filters):
    status = filters["status"] or UserMedia.Status.PLANNED
    entries = UserMedia.objects.filter(user=user, status=status).select_related("media")
    if filters["media_type"]:
        entries = entries.filter(media__media_type=filters["media_type"])
    entries = list(entries.order_by("-created_at")[: filters["limit"]])
    return {"items": _serialize_entries(entries), "status": status, "media_type": filters["media_type"]}


def handle_anime_stats(user, filters):
    return {"result": get_anime_stats(user)}


def handle_estimated_watch_time(user, filters):
    minutes = movie_watch_time(UserMedia.objects.filter(user=user))
    return {"minutes": minutes}


def handle_recommendation(user, filters):
    results, error_code, is_thin_profile = get_recommendations(user, filters["recommendation_text"])
    return {"results": results, "error_code": error_code, "is_thin_profile": is_thin_profile}


INTENT_HANDLERS = {
    "total_library": handle_total_library,
    "count_by_status": handle_count_by_status,
    "count_by_type": handle_count_by_type,
    "average_rating": handle_average_rating,
    "top_rated": handle_top_rated,
    "recently_completed": handle_recently_completed,
    "completed_by_period": handle_completed_by_period,
    "most_active_month": handle_most_active_month,
    "favorites": handle_favorites,
    "items_by_status": handle_items_by_status,
    "anime_stats": handle_anime_stats,
    "estimated_watch_time": handle_estimated_watch_time,
    "recommendation": handle_recommendation,
}
