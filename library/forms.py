from django import forms

from .models import MediaItem, UserMedia

INPUT_CLASSES = (
    "w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 "
    "placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-pink-500"
)
CHECKBOX_CLASSES = "h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-pink-500 focus:ring-pink-500"


class LibrarySearchForm(forms.Form):
    q = forms.CharField(
        label="Título",
        max_length=255,
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Título a buscar..."}),
    )


class MediaItemForm(forms.ModelForm):
    class Meta:
        model = MediaItem
        fields = [
            "title",
            "media_type",
            "release_year",
            "description",
            "duration_minutes",
            "episodes",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "media_type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "release_year": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 4}),
            "duration_minutes": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
            "episodes": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
        }


class UserMediaForm(forms.ModelForm):
    class Meta:
        model = UserMedia
        fields = [
            "status",
            "rating",
            "review",
            "started_at",
            "finished_at",
            "current_episode",
            "favorite",
        ]
        widgets = {
            "status": forms.Select(attrs={"class": INPUT_CLASSES}),
            "rating": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1, "max": 10}),
            "review": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 4}),
            "started_at": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
            "finished_at": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
            "current_episode": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
            "favorite": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASSES}),
        }
