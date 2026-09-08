from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MediaItemForm, UserMediaForm
from .models import MediaItem, UserMedia


def home(request):
    return render(request, "home.html")


@login_required
def library_list(request):
    entries = UserMedia.objects.filter(user=request.user).select_related("media")
    return render(request, "library/list.html", {"entries": entries})


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
