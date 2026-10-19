from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminRole

from . import selectors
from .serializers import OverviewSerializer


class OverviewView(APIView):
    """Admins only: people, learning, revenue and safety across the platform."""

    permission_classes = [IsAdminRole]

    @extend_schema(responses=OverviewSerializer)
    def get(self, request):
        return Response(OverviewSerializer(selectors.overview()).data)
