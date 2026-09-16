"""Análisis avanzado con pandas sobre la biblioteca de un usuario.

Django ORM sigue siendo quien selecciona y filtra los datos (siempre acotado
a `user`). pandas solo entra en juego después, sobre datos ya propios del
usuario, para reutilizar un mismo DataFrame en varios cortes sin repetir
queries. Las estadísticas que ya se resuelven bien con un único aggregate()
(rating medio global, conteos simples...) se quedan en analytics/services.py
y no se migran aquí.
"""

import pandas as pd
from django.db.models import F

from library.models import UserMedia

LIBRARY_COLUMNS = [
    "media_id",
    "title",
    "media_type",
    "status",
    "rating",
    "favorite",
    "started_at",
    "finished_at",
    "created_at",
    "release_year",
    "duration_minutes",
    "episodes",
]


def get_library_dataframe(user):
    """Construye el DataFrame base de la biblioteca de `user`.

    Una sola query (values() + list()), acotada siempre a este usuario.
    Devuelve un DataFrame con las mismas columnas y tipos aunque el usuario
    no tenga ningún registro, para que el resto de funciones no necesiten
    comprobar caso a caso si existen columnas.
    """
    records = list(
        UserMedia.objects.filter(user=user).values(
            "media_id",
            "status",
            "rating",
            "favorite",
            "started_at",
            "finished_at",
            "created_at",
            title=F("media__title"),
            media_type=F("media__media_type"),
            release_year=F("media__release_year"),
            duration_minutes=F("media__duration_minutes"),
            episodes=F("media__episodes"),
        )
    )

    df = pd.DataFrame(records, columns=LIBRARY_COLUMNS)
    df["started_at"] = pd.to_datetime(df["started_at"])
    df["finished_at"] = pd.to_datetime(df["finished_at"])
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["rating"] = pd.to_numeric(df["rating"])
    return df


def monthly_completions(df):
    """Elementos terminados por mes (solo meses con finished_at real)."""
    completed = df.dropna(subset=["finished_at"])
    if completed.empty:
        return []

    counts = (
        completed["finished_at"]
        .dt.to_period("M")
        .value_counts()
        .sort_index()
    )
    return [{"month": str(period), "count": int(count)} for period, count in counts.items()]


def ratings_by_type(df):
    """Nº de ratings, media, máximo y mínimo por media_type. Ignora rating nulo."""
    rated = df.dropna(subset=["rating"])
    if rated.empty:
        return []

    grouped = rated.groupby("media_type")["rating"].agg(["count", "mean", "max", "min"])
    return [
        {
            "media_type": media_type,
            "count": int(row["count"]),
            "average": round(float(row["mean"]), 1),
            "best": int(row["max"]),
            "worst": int(row["min"]),
        }
        for media_type, row in grouped.iterrows()
    ]


def rating_distribution(df):
    """Cuántos elementos tienen cada puntuación (10 -> 6, 9 -> 15...)."""
    rated = df.dropna(subset=["rating"])
    if rated.empty:
        return []

    counts = rated["rating"].value_counts().sort_index(ascending=False)
    return [{"rating": int(rating), "count": int(count)} for rating, count in counts.items()]


def yearly_activity(df):
    """Elementos terminados por año (solo finished_at real)."""
    completed = df.dropna(subset=["finished_at"])
    if completed.empty:
        return []

    counts = completed["finished_at"].dt.year.value_counts().sort_index()
    return [{"year": int(year), "count": int(count)} for year, count in counts.items()]


def busiest_month(df):
    """Mes con más contenido terminado, o None si no hay ninguno."""
    months = monthly_completions(df)
    if not months:
        return None
    return max(months, key=lambda item: item["count"])


def content_type_over_time(df):
    """Tabla cruzada mes x tipo de contenido, solo meses con finished_at real."""
    completed = df.dropna(subset=["finished_at"])
    if completed.empty:
        return []

    completed = completed.copy()
    completed["month"] = completed["finished_at"].dt.to_period("M")

    pivot = completed.pivot_table(
        index="month", columns="media_type", values="media_id", aggfunc="count", fill_value=0
    )
    pivot = pivot.reindex(columns=["movie", "series", "anime"], fill_value=0)
    pivot = pivot.sort_index()

    result = []
    for month, row in pivot.iterrows():
        entry = {"month": str(month)}
        entry.update({media_type: int(count) for media_type, count in row.items()})
        result.append(entry)
    return result


def scoring_habits(df):
    """% de elementos puntuados sobre el total. El resto de hábitos de
    puntuación (media global, por tipo, distribución) ya están cubiertos por
    services.py (ORM) y ratings_by_type()/rating_distribution() de este módulo."""
    total = len(df)
    if total == 0:
        return {"rated_percentage": 0}

    rated_count = df["rating"].notna().sum()
    return {"rated_percentage": round(rated_count / total * 100)}


def get_advanced_stats(user):
    df = get_library_dataframe(user)
    return {
        "monthly_completions": monthly_completions(df),
        "ratings_by_type": ratings_by_type(df),
        "rating_distribution": rating_distribution(df),
        "yearly_activity": yearly_activity(df),
        "busiest_month": busiest_month(df),
        "content_type_over_time": content_type_over_time(df),
        "scoring_habits": scoring_habits(df),
    }
