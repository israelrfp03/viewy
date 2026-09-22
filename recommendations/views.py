from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_recommendations

ERROR_MESSAGES = {
    "not_enough_data": (
        "Aún no tengo suficiente información sobre tus gustos. "
        "Añade y puntúa algunos títulos para obtener recomendaciones personalizadas."
    ),
    "llm_unavailable": "El servicio de recomendaciones no está disponible ahora mismo. Inténtalo de nuevo en un momento.",
    "no_verifiable_results": "No he podido verificar ninguna de las recomendaciones generadas. Inténtalo de nuevo.",
}

REQUEST_TEXT_MAX_LENGTH = 300


@login_required
def recommendations_view(request):
    results = None
    error_message = None
    is_thin_profile = False
    request_text = ""

    if request.method == "POST":
        request_text = request.POST.get("request_text", "").strip()[:REQUEST_TEXT_MAX_LENGTH]
        results, error_code, is_thin_profile = get_recommendations(request.user, request_text)
        if error_code:
            error_message = ERROR_MESSAGES[error_code]

    return render(
        request,
        "recommendations/form.html",
        {
            "results": results,
            "error_message": error_message,
            "is_thin_profile": is_thin_profile,
            "request_text": request_text,
        },
    )
