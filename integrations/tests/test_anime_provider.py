"""Proveedores de enriquecimiento de anime (AniList/Jikan) y el orquestador
que decide entre ellos. Todo mockeado — Viewy debe seguir funcionando
aunque ambos proveedores caigan, tal como se demostró en vivo en la Fase 7.5."""

import requests

from integrations import anilist, anime_provider, jikan


class TestAnimeProviderFallback:
    def test_uses_anilist_when_available_without_touching_jikan(self, monkeypatch):
        monkeypatch.setattr(
            anilist, "search_candidates", lambda q: [anilist.AnimeCandidate("anilist", "1", "X", "X", 2020, "")]
        )
        called = {"jikan": False}

        def fail_jikan(q):
            called["jikan"] = True
            raise jikan.JikanError("no debería llamarse")

        monkeypatch.setattr(jikan, "search_candidates", fail_jikan)

        candidates, provider = anime_provider.search_anime("One Piece")
        assert provider == "anilist"
        assert called["jikan"] is False

    def test_falls_back_to_jikan_when_anilist_fails(self, monkeypatch):
        monkeypatch.setattr(
            anilist, "search_candidates", lambda q: (_ for _ in ()).throw(anilist.AniListError("caído"))
        )
        monkeypatch.setattr(
            jikan, "search_candidates", lambda q: [jikan.AnimeCandidate("jikan", "1", "X", "X", 2020, "")]
        )
        candidates, provider = anime_provider.search_anime("One Piece")
        assert provider == "jikan"
        assert len(candidates) == 1

    def test_raises_provider_unavailable_when_both_fail(self, monkeypatch):
        monkeypatch.setattr(
            anilist, "search_candidates", lambda q: (_ for _ in ()).throw(anilist.AniListError("caído"))
        )
        monkeypatch.setattr(
            jikan, "search_candidates", lambda q: (_ for _ in ()).throw(jikan.JikanError("caído"))
        )
        try:
            anime_provider.search_anime("One Piece")
            assert False, "debería haber lanzado AnimeProviderUnavailable"
        except anime_provider.AnimeProviderUnavailable:
            pass

    def test_get_enrichment_routes_to_correct_provider(self, monkeypatch):
        sentinel = object()
        monkeypatch.setattr(anilist, "get_enrichment", lambda eid: sentinel)
        result = anime_provider.get_anime_enrichment("anilist", "1")
        assert result is sentinel

    def test_unknown_provider_raises_unavailable(self):
        try:
            anime_provider.get_anime_enrichment("proveedor_inventado", "1")
            assert False
        except anime_provider.AnimeProviderUnavailable:
            pass


class TestAniListNormalization:
    def _post(self, monkeypatch, payload, status_code=200):
        def fake_post(*args, **kwargs):
            response = requests.Response()
            response.status_code = status_code
            response.json = lambda: payload
            return response

        monkeypatch.setattr(anilist.requests, "post", fake_post)

    def test_get_enrichment_normalizes_characters_staff_relations(self, monkeypatch):
        from django.core.cache import cache

        cache.clear()
        self._post(
            monkeypatch,
            {
                "data": {
                    "Media": {
                        "id": 37854,
                        "title": {"romaji": "ONE PIECE", "english": "One Piece"},
                        "source": "MANGA",
                        "status": "RELEASING",
                        "studios": {"nodes": [{"name": "Toei Animation"}]},
                        "characters": {
                            "edges": [
                                {
                                    "role": "MAIN",
                                    "node": {
                                        "name": {"full": "Monkey D. Luffy"},
                                        "image": {"medium": "http://x/l.jpg"},
                                        "description": "A pirate ~!secret spoiler!~ who dreams big.",
                                    },
                                    "voiceActors": [{"name": {"full": "Mayumi Tanaka"}}],
                                }
                            ]
                        },
                        "staff": {"edges": [{"role": "Director", "node": {"name": {"full": "Konosuke Uda"}}}]},
                        "relations": {
                            "edges": [
                                {"relationType": "ADAPTATION", "node": {"title": {"romaji": "Manga"}, "type": "MANGA"}},
                                {"relationType": "SEQUEL", "node": {"title": {"romaji": "S2"}, "type": "ANIME"}},
                            ]
                        },
                        "streamingEpisodes": [{"title": "Romance Dawn", "thumbnail": ""}],
                    }
                }
            },
        )
        enrichment = anilist.get_enrichment("37854")
        assert enrichment.characters[0].name == "Monkey D. Luffy"
        assert enrichment.characters[0].voice_actor == "Mayumi Tanaka"
        assert "spoiler" not in enrichment.characters[0].description
        assert enrichment.staff[0].role == "Director"
        # Solo la relación tipo ANIME debe pasar el filtro, nunca la MANGA.
        assert len(enrichment.relations) == 1
        assert enrichment.relations[0].relation_type == "SEQUEL"

    def test_enrichment_is_cached_after_first_call(self, monkeypatch):
        from django.core.cache import cache

        cache.clear()
        call_count = {"n": 0}

        def fake_post(*args, **kwargs):
            call_count["n"] += 1
            response = requests.Response()
            response.status_code = 200
            response.json = lambda: {
                "data": {
                    "Media": {
                        "id": 1, "title": {}, "source": "", "status": "", "studios": {"nodes": []},
                        "characters": {"edges": []}, "staff": {"edges": []}, "relations": {"edges": []},
                        "streamingEpisodes": [],
                    }
                }
            }
            return response

        monkeypatch.setattr(anilist.requests, "post", fake_post)
        anilist.get_enrichment("1")
        anilist.get_enrichment("1")
        anilist.get_enrichment("1")
        assert call_count["n"] == 1

    def test_disabled_api_raises_anilist_error(self, monkeypatch):
        self._post(monkeypatch, {"errors": [{"message": "disabled"}]}, status_code=403)
        try:
            anilist.search_candidates("X")
            assert False
        except anilist.AniListError:
            pass

    def test_timeout_raises_anilist_timeout_error(self, monkeypatch):
        def fake_post(*args, **kwargs):
            raise requests.exceptions.Timeout()

        monkeypatch.setattr(anilist.requests, "post", fake_post)
        try:
            anilist.search_candidates("X")
            assert False
        except anilist.AniListTimeoutError:
            pass

    def test_malformed_response_does_not_crash(self, monkeypatch):
        """Estructura inesperada (KeyError interno) debe traducirse a
        AniListError controlado, nunca propagar un traceback crudo."""
        self._post(monkeypatch, {"data": {}})
        try:
            anilist.search_candidates("X")
            assert False
        except anilist.AniListError:
            pass


class TestJikanNormalization:
    def test_get_enrichment_filters_manga_relations(self, monkeypatch):
        from django.core.cache import cache

        cache.clear()
        responses = {
            "/anime/1": {"data": {"mal_id": 1, "title": "One Piece", "title_english": "One Piece",
                                    "source": "Manga", "status": "Currently Airing", "studios": [{"name": "Toei Animation"}]}},
            "/anime/1/characters": {"data": []},
            "/anime/1/staff": {"data": []},
            "/anime/1/relations": {"data": [
                {"relation": "Adaptation", "entry": [{"name": "Manga", "type": "manga"}]},
                {"relation": "Side Story", "entry": [{"name": "Strong World", "type": "anime"}]},
            ]},
            "/anime/1/episodes": {"data": []},
        }

        def fake_get(url, params=None, timeout=None):
            for path, body in responses.items():
                if url.endswith(path):
                    response = requests.Response()
                    response.status_code = 200
                    response.json = lambda body=body: body
                    return response
            raise AssertionError(f"URL no esperada: {url}")

        monkeypatch.setattr(jikan.requests, "get", fake_get)
        enrichment = jikan.get_enrichment("1")
        assert len(enrichment.relations) == 1
        assert enrichment.relations[0].relation_type == "Side Story"

    def test_upstream_down_raises_jikan_error(self, monkeypatch):
        def fake_get(*args, **kwargs):
            response = requests.Response()
            response.status_code = 504
            response.json = lambda: {}
            return response

        monkeypatch.setattr(jikan.requests, "get", fake_get)
        try:
            jikan.search_candidates("X")
            assert False
        except jikan.JikanError:
            pass
