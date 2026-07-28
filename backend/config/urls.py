from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.media_views import serve_media

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.chats.urls")),
]

# Always register media in DEBUG (custom view works under Daphne/ASGI).
if settings.DEBUG:
    urlpatterns += [
        path("media/<path:path>", serve_media, name="serve-media"),
    ]
