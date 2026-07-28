import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.chats.routing import websocket_urlpatterns  # noqa: E402
from apps.chats.ws_auth import JwtAuthMiddlewareStack  # noqa: E402
from apps.users.bootstrap_dev_users import ensure_dev_users  # noqa: E402

# Temporary local seed — creates alice/bob/charlie when missing (DEBUG only).
ensure_dev_users()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JwtAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
