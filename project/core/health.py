"""GET /healthz/ — for deployment checks: is the app up, which commit, can it reach the database."""
import os

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request):
    """
    200 with the running commit when the database answers; 503 when it doesn't.
    Render sets RENDER_GIT_COMMIT to the deployed commit SHA.
    """
    commit = os.environ.get("RENDER_GIT_COMMIT", "local")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # pylint: disable=broad-exception-caught
        return JsonResponse(
            {"status": "error", "commit": commit, "database": "unreachable"}, status=503
        )
    return JsonResponse({"status": "ok", "commit": commit, "database": "ok"})
