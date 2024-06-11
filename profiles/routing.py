from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/profile/', consumers.ProfileConsumer.as_asgi()),
]