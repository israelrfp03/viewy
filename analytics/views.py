from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_dashboard_stats


@login_required
def dashboard(request):
    stats = get_dashboard_stats(request.user)
    return render(request, "analytics/dashboard.html", {"stats": stats})
