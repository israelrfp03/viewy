from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.home, name="home"),
    path("library/", views.library_list, name="list"),
    path("library/add/", views.media_create, name="create"),
    path("library/search/", views.media_search, name="search"),
    path("library/add-from-tmdb/", views.media_add_from_tmdb, name="add_from_tmdb"),
    path("library/<int:pk>/edit/", views.media_update, name="update"),
    path("library/<int:pk>/delete/", views.media_delete, name="delete"),
    path("library/<int:pk>/", views.entry_detail, name="detail"),
    path("library/<int:pk>/anilist/search/", views.anime_search_candidates, name="anime_search"),
    path("library/<int:pk>/anilist/confirm/", views.anime_confirm_match, name="anime_confirm"),
]
