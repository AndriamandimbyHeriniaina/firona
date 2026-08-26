"""Liveness endpoint used by Docker healthchecks.

Example:
    GET /api/health/ -> {"status": "ok"}
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})
