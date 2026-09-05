from django.conf import settings
from django.db import models


class MediaItem(models.Model):
    class MediaType(models.TextChoices):
        MOVIE = "movie", "Película"
        SERIES = "series", "Serie"
        ANIME = "anime", "Anime"

    class ExternalSource(models.TextChoices):
        MANUAL = "manual", "Manual"
        TMDB = "tmdb", "TMDB"

    title = models.CharField(max_length=255)
    media_type = models.CharField(max_length=10, choices=MediaType.choices, db_index=True)
    release_year = models.PositiveSmallIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    genres = models.JSONField(default=list, blank=True)
    poster_url = models.URLField(blank=True)
    external_id = models.CharField(max_length=100, blank=True)
    external_source = models.CharField(
        max_length=10, choices=ExternalSource.choices, default=ExternalSource.MANUAL, blank=True
    )
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    episodes = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(release_year__gte=1888)
                | models.Q(release_year__isnull=True),
                name="media_item_release_year_reasonable",
            ),
        ]

    def __str__(self):
        return self.title


class UserMedia(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Pendiente"
        WATCHING = "watching", "Viendo"
        COMPLETED = "completed", "Terminado"
        DROPPED = "dropped", "Abandonado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="library_entries")
    media = models.ForeignKey(MediaItem, on_delete=models.CASCADE, related_name="user_entries")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLANNED, db_index=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    review = models.TextField(blank=True)
    started_at = models.DateField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)
    current_episode = models.PositiveIntegerField(default=0)
    favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "media"], name="unique_user_media"),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=10) | models.Q(rating__isnull=True),
                name="user_media_rating_range",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.media}"
