from django import forms

from .models import MediaItem, UserMedia


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
            "started_at": forms.DateInput(attrs={"type": "date"}),
            "finished_at": forms.DateInput(attrs={"type": "date"}),
        }
