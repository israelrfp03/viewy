from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from integrations import tmdb
from integrations.anime_provider import AnimeProviderUnavailable, get_anime_enrichment, search_anime

from .forms import LibrarySearchForm, MediaItemForm, UserMediaForm
from .models import AnimeMetadata, MediaItem, UserMedia
from .queries import DEFAULT_SORT, SORT_LABELS, filter_user_library

LIBRARY_PAGE_SIZE = 12


def home(request):
    return render(request, "home.html")


@login_required
def library_list(request):
    base_queryset = UserMedia.objects.filter(user=request.user).select_related("media")
    entries = filter_user_library(request.GET, base_queryset)

    paginator = Paginator(entries, LIBRARY_PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    querystring = request.GET.copy()
    querystring.pop("page", None)

    context = {
        "page": page,
        "querystring": querystring.urlencode(),
        "statuses": UserMedia.Status.choices,
        "media_types": MediaItem.MediaType.choices,
        "sort_options": SORT_LABELS,
        "current_sort": request.GET.get("sort", DEFAULT_SORT),
        "current_query": request.GET.get("q", ""),
        "current_status": request.GET.get("status", ""),
        "current_media_type": request.GET.get("media_type", ""),
        "current_favorite": request.GET.get("favorite", ""),
    }
    return render(request, "library/list.html", context)


@login_required
def media_create(request):
    if request.method == "POST":
        media_form = MediaItemForm(request.POST)
        entry_form = UserMediaForm(request.POST)

        if media_form.is_valid() and entry_form.is_valid():
            title = media_form.cleaned_data["title"]
            media_type = media_form.cleaned_data["media_type"]
            media = MediaItem.objects.filter(title__iexact=title, media_type=media_type).first()

            if media is None:
                media = media_form.save()

            if UserMedia.objects.filter(user=request.user, media=media).exists():
                entry_form.add_error(None, "Ya tienes este contenido en tu biblioteca.")
            else:
                with transaction.atomic():
                    entry = entry_form.save(commit=False)
                    entry.user = request.user
                    entry.media = media
                    entry.save()
                messages.success(request, "Contenido añadido a tu biblioteca.")
                return redirect("library:list")
    else:
        media_form = MediaItemForm()
        entry_form = UserMediaForm()

    return render(
        request, "library/create.html", {"media_form": media_form, "entry_form": entry_form}
    )


def _get_or_create_media_from_tmdb(detail, media_type):
    """Crea o reutiliza un MediaItem a partir de un detalle de TMDB.

    `media_type` es la clasificación elegida por el usuario (puede ser "anime",
    más específica que el `detail.media_type` base de TMDB). "anime" nunca
    degrada un MediaItem ya clasificado como tal, pero sí puede "mejorar" uno
    que todavía era genérico ("movie"/"series").
    """
    media = MediaItem.objects.filter(
        external_source=MediaItem.ExternalSource.TMDB, external_id=detail.external_id
    ).first()
    if media:
        if media_type == MediaItem.MediaType.ANIME and media.media_type != MediaItem.MediaType.ANIME:
            media.media_type = MediaItem.MediaType.ANIME
            media.save(update_fields=["media_type"])
        return media

    # Reutiliza un MediaItem manual equivalente en vez de duplicar el título.
    media = MediaItem.objects.filter(
        title__iexact=detail.title,
        media_type__in={detail.media_type, media_type},
        external_id="",
    ).first()
    if media:
        media.external_id = detail.external_id
        media.external_source = MediaItem.ExternalSource.TMDB
        media.poster_url = detail.poster_url or media.poster_url
        media.description = detail.description or media.description
        media.release_year = detail.release_year or media.release_year
        media.duration_minutes = detail.duration_minutes or media.duration_minutes
        media.episodes = detail.episodes or media.episodes
        if media_type == MediaItem.MediaType.ANIME:
            media.media_type = MediaItem.MediaType.ANIME
        media.save()
        return media

    return MediaItem.objects.create(
        title=detail.title,
        media_type=media_type,
        release_year=detail.release_year,
        description=detail.description,
        poster_url=detail.poster_url,
        external_id=detail.external_id,
        external_source=MediaItem.ExternalSource.TMDB,
        duration_minutes=detail.duration_minutes,
        episodes=detail.episodes,
    )


@login_required
def media_search(request):
    form = LibrarySearchForm(request.GET or None)
    results = []
    searched = False

    if form.is_valid():
        searched = True
        try:
            results = tmdb.search(form.cleaned_data["q"])
        except tmdb.TMDBError:
            messages.error(request, "TMDB no está disponible ahora mismo, inténtalo más tarde.")

    return render(
        request, "library/search.html", {"form": form, "results": results, "searched": searched}
    )


@login_required
def media_add_from_tmdb(request):
    if request.method != "POST":
        return redirect("library:search")

    external_id = request.POST.get("external_id", "")
    source_type = request.POST.get("source_type", "")
    media_type = request.POST.get("media_type", "")

    if (
        not external_id
        or source_type not in ("movie", "tv")
        or media_type not in MediaItem.MediaType.values
    ):
        messages.error(request, "Selección no válida.")
        return redirect("library:search")

    try:
        detail = tmdb.get_detail(external_id, source_type)
    except tmdb.TMDBError:
        messages.error(request, "No se pudo obtener la información de TMDB. Inténtalo de nuevo.")
        return redirect("library:search")

    with transaction.atomic():
        media = _get_or_create_media_from_tmdb(detail, media_type)

        if UserMedia.objects.filter(user=request.user, media=media).exists():
            messages.info(request, "Ya tienes este contenido en tu biblioteca.")
        else:
            UserMedia.objects.create(user=request.user, media=media)
            messages.success(request, "Añadido a tu biblioteca.")

    return redirect("library:list")


@login_required
def media_update(request, pk):
    entry = get_object_or_404(UserMedia, pk=pk, user=request.user)

    if request.method == "POST":
        form = UserMediaForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro actualizado.")
            return redirect("library:list")
    else:
        form = UserMediaForm(instance=entry)

    return render(request, "library/edit.html", {"form": form, "entry": entry})


@login_required
def media_delete(request, pk):
    entry = get_object_or_404(UserMedia, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        messages.success(request, "Registro eliminado.")
        return redirect("library:list")

    return render(request, "library/confirm_delete.html", {"entry": entry})


@login_required
def entry_detail(request, pk):
    entry = get_object_or_404(UserMedia, pk=pk, user=request.user)
    media = entry.media

    anime_metadata = None
    enrichment = None
    anime_provider_unavailable = False

    if media.media_type == MediaItem.MediaType.ANIME:
        anime_metadata = getattr(media, "anime_metadata", None)
        if anime_metadata:
            try:
                enrichment = get_anime_enrichment(
                    anime_metadata.external_source, anime_metadata.external_id
                )
            except AnimeProviderUnavailable:
                anime_provider_unavailable = True

    context = {
        "entry": entry,
        "media": media,
        "anime_metadata": anime_metadata,
        "enrichment": enrichment,
        "anime_provider_unavailable": anime_provider_unavailable,
    }
    return render(request, "library/detail.html", context)


@login_required
def anime_search_candidates(request, pk):
    entry = get_object_or_404(UserMedia, pk=pk, user=request.user)
    media = entry.media

    if media.media_type != MediaItem.MediaType.ANIME:
        messages.error(request, "Solo se puede enriquecer contenido de tipo anime.")
        return redirect("library:detail", pk=pk)

    query = request.GET.get("q", media.title)
    candidates = []
    used_provider = None
    anime_provider_unavailable = False

    try:
        candidates, used_provider = search_anime(query)
    except AnimeProviderUnavailable:
        anime_provider_unavailable = True
        messages.error(
            request, "Ni AniList ni Jikan están disponibles ahora mismo, inténtalo más tarde."
        )

    context = {
        "entry": entry,
        "media": media,
        "query": query,
        "candidates": candidates,
        "used_provider": used_provider,
        "anime_provider_unavailable": anime_provider_unavailable,
    }
    return render(request, "library/anime_search.html", context)


@login_required
def anime_confirm_match(request, pk):
    entry = get_object_or_404(UserMedia, pk=pk, user=request.user)
    media = entry.media

    if request.method != "POST" or media.media_type != MediaItem.MediaType.ANIME:
        return redirect("library:detail", pk=pk)

    external_id = request.POST.get("external_id", "")
    source = request.POST.get("source", "")
    if not external_id or source not in ("anilist", "jikan"):
        messages.error(request, "Selección no válida.")
        return redirect("library:anime_search", pk=pk)

    try:
        enrichment = get_anime_enrichment(source, external_id)
    except AnimeProviderUnavailable:
        messages.error(request, "No se pudo obtener la información. Inténtalo de nuevo.")
        return redirect("library:anime_search", pk=pk)

    existing = AnimeMetadata.objects.filter(
        external_source=source, external_id=external_id
    ).exclude(media=media).first()
    if existing:
        messages.error(request, "Ese anime ya está asociado a otro elemento de tu catálogo.")
        return redirect("library:anime_search", pk=pk)

    AnimeMetadata.objects.update_or_create(
        media=media,
        defaults={
            "external_source": source,
            "external_id": enrichment.external_id,
            "title_romaji": enrichment.title_romaji,
            "title_english": enrichment.title_english,
            "source_material": enrichment.source_material,
            "studio": enrichment.studio,
        },
    )
    messages.success(request, f"Anime enriquecido con datos de {source}.")
    return redirect("library:detail", pk=pk)
