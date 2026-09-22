from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .services import answer_question

MAX_HISTORY = 10
QUESTION_MAX_LENGTH = 300


@login_required
def chat_view(request):
    history = request.session.get("assistant_history", [])

    if request.method == "POST":
        if request.POST.get("action") == "clear":
            request.session["assistant_history"] = []
            return redirect("assistant:chat")

        question = request.POST.get("question", "").strip()[:QUESTION_MAX_LENGTH]
        if question:
            answer, error_code = answer_question(request.user, question)
            history = history + [{"question": question, "answer": answer, "error": bool(error_code)}]
            history = history[-MAX_HISTORY:]
            request.session["assistant_history"] = history

    return render(request, "assistant/chat.html", {"history": history})
