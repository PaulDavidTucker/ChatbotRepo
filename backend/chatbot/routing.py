from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/chat/<str:api_key>/", consumers.ChatConsumer.as_asgi()),
]
