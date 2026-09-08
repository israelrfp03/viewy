from django.contrib import admin

from .models import AnimeMetadata, MediaItem, UserMedia


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ("title", "media_type", "release_year", "external_source")
    list_filter = ("media_type", "external_source")
    search_fields = ("title",)


@admin.register(UserMedia)
class UserMediaAdmin(admin.ModelAdmin):
    list_display = ("user", "media", "status", "rating", "favorite")
    list_filter = ("status", "favorite")
    search_fields = ("user__username", "media__title")
    autocomplete_fields = ("user", "media")


@admin.register(AnimeMetadata)
class AnimeMetadataAdmin(admin.ModelAdmin):
    list_display = ("media", "title_english", "studio", "source_material")
    search_fields = ("media__title", "title_romaji", "title_english")
    autocomplete_fields = ("media",)
