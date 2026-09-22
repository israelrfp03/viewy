from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .chart_data import build_chart_data
from .services import get_dashboard_stats


@login_required
def dashboard(request):
    stats = get_dashboard_stats(request.user)
    chart_data = build_chart_data(stats)
    return render(request, "analytics/dashboard.html", {"stats": stats, "chart_data": chart_data})
