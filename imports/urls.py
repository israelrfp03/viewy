from django.urls import path

from . import views

app_name = "imports"

urlpatterns = [
    path("", views.start_view, name="start"),
    path("preview/", views.preview_view, name="preview"),
    path("result/", views.result_view, name="result"),
]
