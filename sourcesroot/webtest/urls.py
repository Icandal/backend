from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def api_root(request):
    return JsonResponse({
        "message": "Flanker Task API",
        "endpoints": {
            "register": "/api/register/",
            "session_start": "/api/session/start/",
            "block_create": "/api/block/create/",
            "trials_batch": "/api/trials/batch/",
            "block_complete": "/api/block/complete/",
            "session_complete": "/api/session/complete/",
            "health": "/api/health/",
        },
        "timestamp": timezone.now().isoformat(),
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("testapp.urls")),
    path("", api_root, name="api-root"),
]