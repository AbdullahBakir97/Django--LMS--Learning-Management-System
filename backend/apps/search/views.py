from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors
from .serializers import HitSerializer, hits

Results = inline_serializer(
    "SearchResults",
    {kind: HitSerializer(many=True, required=False) for kind in selectors.KINDS},
)


class SearchView(APIView):
    """GET /api/search/?q=django → up to 5 of each kind; add &type=jobs for up to 20 jobs."""

    @extend_schema(
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR, required=True),
            OpenApiParameter("type", OpenApiTypes.STR, enum=list(selectors.KINDS)),
        ],
        responses=Results,
    )
    def get(self, request):
        text = request.query_params.get("q", "")[:100]
        kind = request.query_params.get("type")
        if kind and kind not in selectors.KINDS:
            raise serializers.ValidationError({"type": f"One of: {', '.join(selectors.KINDS)}."})
        kinds, limit = ((kind,), 20) if kind else (selectors.KINDS, 5)
        found = selectors.search(request.user, text, kinds, limit)
        return Response({k: hits(k, rows) for k, rows in found.items()})
