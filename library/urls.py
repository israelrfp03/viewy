from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.home, name="home"),
    path("library/", views.library_list, name="list"),
    path("library/add/", views.media_create, name="create"),
    path("library/<int:pk>/edit/", views.media_update, name="update"),
    path("library/<int:pk>/delete/", views.media_delete, name="delete"),
]
