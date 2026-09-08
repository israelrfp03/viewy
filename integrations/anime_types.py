"""Estructuras normalizadas compartidas por los proveedores de enriquecimiento de anime.

Tanto integrations/anilist.py como integrations/jikan.py devuelven estos mismos
tipos, para que el resto de la aplicación (views, templates) no necesite saber
de qué proveedor concreto vinieron los datos.
"""

from dataclasses import dataclass, field


@dataclass
class AnimeCandidate:
    source: str  # "anilist" | "jikan"
    external_id: str
    title_romaji: str
    title_english: str
    release_year: int | None
    poster_url: str


@dataclass
class AnimeCharacter:
    name: str
    image_url: str
    role: str
    voice_actor: str
    description: str


@dataclass
class AnimeStaffMember:
    name: str
    role: str


@dataclass
class AnimeRelation:
    title: str
    relation_type: str


@dataclass
class AnimeEpisode:
    number: int
    title: str
    thumbnail_url: str


@dataclass
class AnimeEnrichment:
    external_id: str
    title_romaji: str
    title_english: str
    source_material: str
    studio: str
    status: str
    characters: list = field(default_factory=list)
    staff: list = field(default_factory=list)
    relations: list = field(default_factory=list)
    episodes: list = field(default_factory=list)
