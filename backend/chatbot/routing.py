from django.urls import path
from . import consumers
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")


websocket_urlpatterns = [
    path("ws/chat/<str:api_key>/", consumers.ChatConsumer.as_asgi()),
    path("ws/chat/", consumers.ChatConsumer.as_asgi()),
]
