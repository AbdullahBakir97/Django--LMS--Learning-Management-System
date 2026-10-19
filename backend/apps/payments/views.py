from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.learning.models import Course

from . import services

CheckoutIn = inline_serializer("CheckoutRequest", {"course": serializers.SlugField()})
CheckoutOut = inline_serializer("CheckoutPage", {"url": serializers.URLField()})


class CheckoutView(APIView):
    """Start paying for a course. Send the browser to the returned URL."""

    @extend_schema(request=CheckoutIn, responses=CheckoutOut)
    def post(self, request):
        slug = serializers.SlugField().run_validation(request.data.get("course"))
        course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)
        return Response({"url": services.start_checkout(request.user, course)})


class WebhookView(APIView):
    """Stripe calls this. The signature, not a session, proves who is calling."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        event = services.parse_event(request.body, request.headers.get("Stripe-Signature"))
        services.handle_event(event)
        return Response()
