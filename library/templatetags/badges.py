from django import template

register = template.Library()

_LABELS = {"planned": "Pendiente", "watching": "Viendo", "completed": "Terminado", "dropped": "Abandonado"}
_DOT = {"planned": "bg-planned", "watching": "bg-watching", "completed": "bg-completed", "dropped": "bg-dropped"}
_BG = {"planned": "bg-planned-bg", "watching": "bg-watching-bg", "completed": "bg-completed-bg", "dropped": "bg-dropped-bg"}
_FG = {"planned": "text-planned-fg", "watching": "text-watching-fg", "completed": "text-completed-fg", "dropped": "text-dropped-fg"}


@register.filter
def status_label(status):
    return _LABELS.get(status, status)


@register.filter
def status_dot(status):
    return _DOT.get(status, "bg-faint")


@register.filter
def status_bg(status):
    return _BG.get(status, "bg-paper")


@register.filter
def status_fg(status):
    return _FG.get(status, "text-muted")


@register.filter
def rating_color(rating):
    if rating is None:
        return "text-faint"
    if rating >= 8:
        return "text-brand-500"
    if rating >= 5:
        return "text-ink"
    return "text-dropped"
