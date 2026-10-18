from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.fields import CharField
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .realtime import issue_ticket


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: dict, 503: dict})
    def get(self, request):
        checks = {"database": _check(connection.ensure_connection), "cache": _check(_ping_cache)}
        ok = all(checks.values())
        return Response({"status": "ok" if ok else "degraded", **checks}, status=200 if ok else 503)


def _ping_cache():
    cache.set("health", "1", 5)
    assert cache.get("health") == "1"


def _check(fn) -> bool:
    try:
        fn()
    except Exception:
        return False
    return True


class RealtimeTicketView(APIView):
    """A 30-second ticket to open the events WebSocket: `/ws/events/?ticket=<ticket>`."""

    @extend_schema(request=None, responses=inline_serializer("Ticket", {"ticket": CharField()}))
    def post(self, request):
        return Response({"ticket": issue_ticket(request.user)})
