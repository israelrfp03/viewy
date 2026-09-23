from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from library.models import MediaItem, UserMedia

from .services import MAX_ITEMS, analyze_text, confirm_import

TEXT_MAX_LENGTH = 20000  # límite defensivo de longitud del texto pegado
SESSION_ROWS_KEY = "import_preview_rows"
SESSION_SUMMARY_KEY = "import_summary"


@login_required
def start_view(request):
    if request.method == "POST":
        text = request.POST.get("text", "")[:TEXT_MAX_LENGTH]
        if not text.strip():
            messages.error(request, "Pega algo de texto para poder analizarlo.")
            return render(request, "imports/start.html")

        rows, truncated = analyze_text(request.user, text)
        if not rows:
            messages.error(request, "No se ha podido interpretar ninguna línea de ese texto.")
            return render(request, "imports/start.html")

        if truncated:
            messages.info(
                request, f"Se han analizado los primeros {MAX_ITEMS} elementos; el resto se ha descartado."
            )

        request.session[SESSION_ROWS_KEY] = rows
        return redirect("imports:preview")

    return render(request, "imports/start.html")


@login_required
def preview_view(request):
    rows = request.session.get(SESSION_ROWS_KEY)
    if not rows:
        messages.error(request, "No hay ninguna importación en curso. Empieza pegando tu lista.")
        return redirect("imports:start")

    if request.method == "POST":
        updated_rows = _read_corrections(request.POST, rows)
        summary = confirm_import(request.user, updated_rows)
        del request.session[SESSION_ROWS_KEY]
        request.session[SESSION_SUMMARY_KEY] = summary
        return redirect("imports:result")

    return render(
        request,
        "imports/preview.html",
        {
            "rows": list(enumerate(rows)),
            "media_types": MediaItem.MediaType.choices,
            "statuses": UserMedia.Status.choices,
        },
    )


@login_required
def result_view(request):
    summary = request.session.pop(SESSION_SUMMARY_KEY, None)
    if summary is None:
        return redirect("imports:start")
    return render(request, "imports/result.html", {"summary": summary})


def _read_corrections(post_data, rows):
    updated = []
    for i, row in enumerate(rows):
        row = dict(row)
        row["excluded"] = post_data.get(f"exclude_{i}") == "on"
        row["title"] = post_data.get(f"title_{i}", row["title"]).strip()[:255]

        rating_raw = post_data.get(f"rating_{i}", "").strip()
        if rating_raw:
            try:
                rating = float(rating_raw.replace(",", "."))
                row["rating"] = rating if 1 <= rating <= 10 else None
            except ValueError:
                row["rating"] = None
        else:
            row["rating"] = None

        media_type = post_data.get(f"media_type_{i}")
        if media_type in MediaItem.MediaType.values:
            row["media_type"] = media_type

        status = post_data.get(f"status_{i}")
        if status in UserMedia.Status.values:
            row["status"] = status

        candidate_choice = post_data.get(f"candidate_{i}")
        if candidate_choice:
            chosen = next((c for c in row["candidates"] if c["external_id"] == candidate_choice), None)
            if chosen:
                row["selected_external_id"] = chosen["external_id"]
                row["selected_source_type"] = chosen["source_type"]
                row["media_type"] = chosen["media_type"]
                row["match_state"] = "matched"

        duplicate_action = post_data.get(f"duplicate_action_{i}")
        if duplicate_action in ("ignore", "update"):
            row["duplicate_action"] = duplicate_action

        updated.append(row)
    return updated
