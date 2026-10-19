from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminRole

from . import selectors
from .serializers import OverviewSerializer

CACHE_KEY = "insights:overview"


class OverviewView(APIView):
    """Admins only: people, learning, revenue and safety across the platform."""

    permission_classes = [IsAdminRole]

    @extend_schema(responses=OverviewSerializer)
    def get(self, request):
        # Nobody needs these to the second; one admin's refresh serves the rest for a while.
        data = cache.get_or_set(
            CACHE_KEY, lambda: OverviewSerializer(selectors.overview()).data, 120
        )
        return Response(data)
