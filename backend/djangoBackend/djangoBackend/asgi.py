"""
ASGI config for djangoBackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import django
import vizStudio.routing


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoBackend.settings")
django.setup()
application = get_asgi_application()
# from django.conf import settings

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            vizStudio.routing.websocket_urlpatterns
        )
    ),
})