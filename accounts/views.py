from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from analytics.services import get_dashboard_stats, get_favorites
from library.models import MediaItem, UserMedia

from .forms import RegisterForm

STATUS_VERBS = {
    UserMedia.Status.COMPLETED: "Terminó",
    UserMedia.Status.WATCHING: "Avanzó en",
    UserMedia.Status.PLANNED: "Añadió",
    UserMedia.Status.DROPPED: "Abandonó",
}


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente. Ya puedes iniciar sesión.")
            return redirect("accounts:login")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    stats = get_dashboard_stats(request.user)

    most_watched_type = None
    if stats["media_type_breakdown"]:
        most_watched_type = max(
            stats["media_type_breakdown"].values(), key=lambda data: data["count"]
        )

    best_rated_type = None
    if stats["advanced"]["ratings_by_type"]:
        best_row = max(stats["advanced"]["ratings_by_type"], key=lambda row: row["average"])
        best_rated_type = dict(MediaItem.MediaType.choices).get(best_row["media_type"])

    dropout_rate = None
    if stats["total"]:
        dropout_rate = round(stats["status_counts"]["dropped"] / stats["total"] * 100)

    top_studio = None
    if stats["anime_stats"] and stats["anime_stats"].get("top_studio"):
        top_studio = stats["anime_stats"]["top_studio"]["studio"]

    # CONTEXTO NUEVO (fase 10 del rediseño): últimas 5 entradas por
    # updated_at, con un verbo derivado del estado, para "Actividad reciente".
    recent_activity = []
    for entry in (
        UserMedia.objects.filter(user=request.user)
        .select_related("media")
        .order_by("-updated_at")[:5]
    ):
        recent_activity.append({"entry": entry, "verb": STATUS_VERBS.get(entry.status, "Actualizó")})

    has_recent_activity = bool(
        recent_activity
        and recent_activity[0]["entry"].updated_at
        >= timezone.now() - timezone.timedelta(days=14)
    )

    context = {
        "stats": stats,
        "most_watched_type": most_watched_type,
        "best_rated_type": best_rated_type,
        "dropout_rate": dropout_rate,
        "top_studio": top_studio,
        "favorites": get_favorites(request.user, limit=4),
        "recent_activity": recent_activity,
        "has_recent_activity": has_recent_activity,
    }
    return render(request, "accounts/profile.html", context)
