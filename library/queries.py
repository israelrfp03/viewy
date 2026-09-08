from django.db.models import Q

from .models import MediaItem, UserMedia

SORT_OPTIONS = {
    "recent": "-created_at",
    "oldest": "created_at",
    "title_asc": "media__title",
    "title_desc": "-media__title",
    "rating_desc": "-rating",
    "rating_asc": "rating",
    "finished_recent": "-finished_at",
}
SORT_LABELS = [
    ("recent", "Añadidos recientemente"),
    ("oldest", "Añadidos hace más tiempo"),
    ("title_asc", "Título (A-Z)"),
    ("title_desc", "Título (Z-A)"),
    ("rating_desc", "Mejor puntuación"),
    ("rating_asc", "Peor puntuación"),
    ("finished_recent", "Finalizados recientemente"),
]
DEFAULT_SORT = "recent"

STATUS_VALUES = set(UserMedia.Status.values)
MEDIA_TYPE_VALUES = set(MediaItem.MediaType.values)


def filter_user_library(get_params, queryset):
    """Aplica búsqueda, filtros y orden a un queryset de UserMedia a partir de request.GET."""
    query = get_params.get("q", "").strip()
    if query:
        queryset = queryset.filter(Q(media__title__icontains=query))

    status = get_params.get("status", "")
    if status in STATUS_VALUES:
        queryset = queryset.filter(status=status)

    media_type = get_params.get("media_type", "")
    if media_type in MEDIA_TYPE_VALUES:
        queryset = queryset.filter(media__media_type=media_type)

    if get_params.get("favorite") == "1":
        queryset = queryset.filter(favorite=True)

    sort = get_params.get("sort", DEFAULT_SORT)
    order_field = SORT_OPTIONS.get(sort, SORT_OPTIONS[DEFAULT_SORT])

    return queryset.order_by(order_field, "-id")
