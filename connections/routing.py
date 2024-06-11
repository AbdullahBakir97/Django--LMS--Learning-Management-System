from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/connection/(?P<room_name>\w+)/$', consumers.ConnectionConsumer.as_asgi()),
]