from datetime import date, timedelta
from typing import NamedTuple

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from integrations import tmdb
from library.models import UserMedia
from library.services import get_or_create_media_from_tmdb

DEMO_USERNAME = "demo"


class DemoEntry(NamedTuple):
    source_type: str
    tmdb_id: str
    media_type: str
    status: str
    rating: int | None = None
    started_days_ago: int | None = None
    finished_days_ago: int | None = None
    favorite: bool = False
    current_episode: int = 0
    review: str = ""


DEMO_LIBRARY = [
    DemoEntry("movie", "157336", "movie", "completed", 10, 20, 20, True, review="Me sigue volando la cabeza."),
    DemoEntry("tv", "1396", "series", "completed", 10, 400, 330, True),
    DemoEntry("tv", "70523", "series", "completed", 9, 250, 220),
    DemoEntry("tv", "87108", "series", "completed", 10, 120, 115, review="Cinco episodios perfectos."),
    DemoEntry("movie", "496243", "movie", "completed", 9, 90, 90),
    DemoEntry("movie", "155", "movie", "completed", 9, 150, 150),
    DemoEntry("movie", "27205", "movie", "completed", 8, 45, 45),
    DemoEntry("movie", "603", "movie", "completed", 8, 380, 380),
    DemoEntry("movie", "129", "anime", "completed", 9, 60, 60, True),
    DemoEntry("movie", "372058", "anime", "completed", 8, 10, 10),
    DemoEntry("tv", "1429", "anime", "completed", 9, 300, 200),
    DemoEntry("tv", "31911", "anime", "completed", 10, 700, 640, True),
    DemoEntry("tv", "37854", "anime", "watching", 9, 500, current_episode=650),
    DemoEntry("tv", "94605", "series", "watching", started_days_ago=15, current_episode=6),
    DemoEntry("tv", "66732", "series", "watching", 7, 40, current_episode=20),
    DemoEntry("tv", "1399", "series", "dropped", 6, 600, current_episode=45,
              review="La última temporada me quitó las ganas."),
    DemoEntry("tv", "13916", "anime", "planned"),
    DemoEntry("movie", "438631", "movie", "planned"),
]


def _days_ago(days):
    return date.today() - timedelta(days=days) if days is not None else None


class Command(BaseCommand):
    help = "Crea o restablece la cuenta demo con una biblioteca de ejemplo (datos reales de TMDB)."

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True)

    def handle(self, *args, password, **options):
        # Se piden todos los detalles antes de escribir: si TMDB falla a mitad,
        # la cuenta demo queda como estaba en vez de a medio rellenar.
        fetched = []
        for entry in DEMO_LIBRARY:
            try:
                fetched.append((entry, tmdb.get_detail(entry.tmdb_id, entry.source_type)))
            except tmdb.TMDBError as exc:
                raise CommandError(f"TMDB falló con {entry.source_type}/{entry.tmdb_id}: {exc}") from exc

        with transaction.atomic():
            user, created = get_user_model().objects.get_or_create(username=DEMO_USERNAME)
            user.set_password(password)
            user.save()
            user.library_entries.all().delete()

            for entry, detail in fetched:
                UserMedia.objects.create(
                    user=user,
                    media=get_or_create_media_from_tmdb(detail, entry.media_type),
                    status=entry.status,
                    rating=entry.rating,
                    review=entry.review,
                    started_at=_days_ago(entry.started_days_ago),
                    finished_at=_days_ago(entry.finished_days_ago),
                    current_episode=entry.current_episode,
                    favorite=entry.favorite,
                )
                self.stdout.write(f"  {detail.title}")

        action = "creada" if created else "restablecida"
        self.stdout.write(self.style.SUCCESS(f"Cuenta demo {action} con {len(fetched)} títulos."))
