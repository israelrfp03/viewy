from io import StringIO
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from integrations import tmdb
from integrations.tmdb import TMDBDetail
from library.management.commands.seed_demo import DEMO_LIBRARY, DEMO_USERNAME
from library.models import UserMedia

pytestmark = pytest.mark.django_db


def _fake_detail(external_id, source_type):
    media_type = "movie" if source_type == "movie" else "series"
    return TMDBDetail(external_id, source_type, media_type, f"Título {external_id}", 2020, "", "", False, None, None)


def _seed(password="demo-pass"):
    with patch("library.management.commands.seed_demo.tmdb.get_detail", side_effect=_fake_detail):
        call_command("seed_demo", password=password, stdout=StringIO())


def test_creates_demo_user_with_full_library():
    _seed()
    user = get_user_model().objects.get(username=DEMO_USERNAME)
    assert user.check_password("demo-pass")
    assert UserMedia.objects.filter(user=user).count() == len(DEMO_LIBRARY)


def test_rerun_resets_library_instead_of_duplicating():
    _seed()
    user = get_user_model().objects.get(username=DEMO_USERNAME)
    UserMedia.objects.filter(user=user).update(rating=1)
    _seed()
    entries = UserMedia.objects.filter(user=user)
    assert entries.count() == len(DEMO_LIBRARY)
    assert not entries.filter(rating=1).exists()


def test_tmdb_failure_leaves_existing_demo_untouched():
    _seed()
    with patch("library.management.commands.seed_demo.tmdb.get_detail", side_effect=tmdb.TMDBError("caído")):
        with pytest.raises(CommandError):
            call_command("seed_demo", password="otra")
    user = get_user_model().objects.get(username=DEMO_USERNAME)
    assert user.check_password("demo-pass")
    assert UserMedia.objects.filter(user=user).count() == len(DEMO_LIBRARY)
