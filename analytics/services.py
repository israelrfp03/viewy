from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.db.models.functions import ExtractYear
from django.utils import timezone

from library.models import AnimeMetadata, MediaItem, UserMedia

from .dataframes import get_advanced_stats


def get_dashboard_stats(user):
    """Calcula todas las estadísticas del dashboard, únicamente sobre los
    UserMedia del usuario dado. Nunca debe recibir ni usar un user_id externo.

    "advanced" viene de dataframes.py (pandas); el resto de claves vienen de
    este módulo (Django ORM) — se mantienen separadas a propósito para que
    quede claro qué herramienta calculó cada cosa.
    """
    queryset = UserMedia.objects.filter(user=user)
    total = queryset.count()

    return {
        "total": total,
        "status_counts": status_counts(queryset),
        "media_type_breakdown": media_type_breakdown(queryset, total),
        "favorites": queryset.filter(favorite=True).count(),
        "rating_stats": rating_stats(queryset),
        "temporal_stats": _temporal_stats(queryset),
        "movie_watch_minutes": movie_watch_time(queryset),
        "average_watch_days": _average_watch_duration(queryset),
        "recent_completed": recent_completed(queryset),
        "anime_stats": anime_stats(user),
        "advanced": get_advanced_stats(user),
    }


def status_counts(queryset):
    """Un único aggregate() con conteo condicional por estado, en vez de
    cuatro .filter().count() separados (cuatro queries)."""
    return queryset.aggregate(
        planned=Count("id", filter=Q(status=UserMedia.Status.PLANNED)),
        watching=Count("id", filter=Q(status=UserMedia.Status.WATCHING)),
        completed=Count("id", filter=Q(status=UserMedia.Status.COMPLETED)),
        dropped=Count("id", filter=Q(status=UserMedia.Status.DROPPED)),
    )


def media_type_breakdown(queryset, total):
    """Patrón values().annotate(): agrupa por tipo de contenido en una sola query."""
    rows = queryset.values("media__media_type").annotate(count=Count("id"))
    counts_by_type = {row["media__media_type"]: row["count"] for row in rows}

    breakdown = {}
    for value, label in MediaItem.MediaType.choices:
        count = counts_by_type.get(value, 0)
        breakdown[value] = {
            "label": label,
            "count": count,
            "percentage": round(count / total * 100) if total else 0,
        }
    return breakdown


def rating_stats(queryset):
    """Avg/Max/Min/Count(campo) ignoran NULL automáticamente: los elementos
    sin puntuar no distorsionan la media ni se cuentan como puntuados."""
    stats = queryset.aggregate(
        average=Avg("rating"),
        best=Max("rating"),
        worst=Min("rating"),
        rated_count=Count("rating"),
    )
    if stats["average"] is not None:
        stats["average"] = round(stats["average"], 1)
    return stats


def _temporal_stats(queryset):
    now = timezone.now()
    completed = queryset.filter(status=UserMedia.Status.COMPLETED, finished_at__isnull=False)

    best_year = (
        completed.annotate(year=ExtractYear("finished_at"))
        .values("year")
        .annotate(count=Count("id"))
        .order_by("-count", "-year")
        .first()
    )

    return {
        "completed_this_year": completed.filter(finished_at__year=now.year).count(),
        "completed_this_month": completed.filter(
            finished_at__year=now.year, finished_at__month=now.month
        ).count(),
        "best_year": best_year,  # {"year": ..., "count": ...} o None si no hay completados
    }


def movie_watch_time(queryset):
    """Solo películas: duration_minutes representa duración total y de forma
    fiable únicamente ahí (ver documentación de la Fase 8 sobre por qué no
    se estima para series/anime)."""
    result = queryset.filter(
        status=UserMedia.Status.COMPLETED,
        media__media_type=MediaItem.MediaType.MOVIE,
        media__duration_minutes__isnull=False,
    ).aggregate(total=Sum("media__duration_minutes"))
    return result["total"]


def _average_watch_duration(queryset):
    """Días de media entre started_at y finished_at, calculado con F()
    dentro de la base de datos. Se descartan fechas inconsistentes
    (finished_at anterior a started_at) porque el modelo no lo impide."""
    valid = queryset.filter(
        started_at__isnull=False,
        finished_at__isnull=False,
        finished_at__gte=F("started_at"),
    ).annotate(watch_duration=F("finished_at") - F("started_at"))

    result = valid.aggregate(avg=Avg("watch_duration"))
    avg = result["avg"]
    return avg.days if avg is not None else None


def recent_completed(queryset, media_type=None, limit=5):
    """Solo elementos con finished_at conocido: sin fecha no hay "reciente" que
    ordenar, y el orden de los NULL en DESC no es portable entre motores de BD."""
    entries = queryset.filter(status=UserMedia.Status.COMPLETED, finished_at__isnull=False)
    if media_type:
        entries = entries.filter(media__media_type=media_type)
    return entries.select_related("media").order_by("-finished_at")[:limit]


def anime_stats(user):
    """Solo se calcula si el usuario tiene algún anime enriquecido — el
    enriquecimiento es opcional (Fase 7.5), así que puede no haber ninguno."""
    anime_metadata = AnimeMetadata.objects.filter(media__user_entries__user=user)
    if not anime_metadata.exists():
        return None

    top_studio = (
        anime_metadata.exclude(studio="")
        .values("studio")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )
    top_source = (
        anime_metadata.exclude(source_material="")
        .values("source_material")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )
    return {"top_studio": top_studio, "top_source": top_source}


def get_top_rated(user, media_type=None, limit=5):
    """Elementos con rating no nulo, mejor puntuados primero. Reutilizada por
    recommendations (Fase 11) y por el asistente (Fase 12) — evita mantener
    la misma consulta escrita dos veces."""
    entries = UserMedia.objects.filter(user=user, rating__isnull=False).select_related("media")
    if media_type:
        entries = entries.filter(media__media_type=media_type)
    return list(entries.order_by("-rating")[:limit])


def get_favorites(user, media_type=None, limit=8):
    """Elementos marcados como favoritos."""
    entries = UserMedia.objects.filter(user=user, favorite=True).select_related("media")
    if media_type:
        entries = entries.filter(media__media_type=media_type)
    return list(entries.order_by("-created_at")[:limit])
