from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminRole

from . import selectors, services
from .models import Report
from .serializers import QueueItemSerializer, ReportCreateSerializer, ResolveSerializer

Resolved = inline_serializer("ReportsResolved", {"resolved": serializers.IntegerField()})


class ReportView(APIView):
    """Report a post, a comment or a person. Reporting the same thing twice changes nothing."""

    @extend_schema(request=ReportCreateSerializer, responses={201: None, 200: None})
    def post(self, request):
        data = ReportCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        _, created = services.report(request.user, **data.validated_data)
        return Response(status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class QueueView(APIView):
    """Staff only: open reports, grouped by what they are about, oldest first."""

    permission_classes = [IsAdminRole]

    @extend_schema(responses=QueueItemSerializer(many=True))
    def get(self, request):
        return Response(QueueItemSerializer(selectors.queue(), many=True).data)


class ResolveView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(request=ResolveSerializer, responses=Resolved)
    def post(self, request, kind, object_id):
        if kind not in Report.Kind.values:
            raise serializers.ValidationError({"kind": "Unknown kind."})
        data = ResolveSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        count = services.resolve(
            request.user,
            kind,
            object_id,
            remove=data.validated_data["action"] == "remove",
            note=data.validated_data["note"],
        )
        return Response({"resolved": count})
