from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors, services
from .models import Company
from .serializers import (
    AddMemberSerializer,
    ApplicationSerializer,
    ApplySerializer,
    CompanySerializer,
    JobSerializer,
    MemberSerializer,
    StatusSerializer,
)

User = get_user_model()


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    lookup_field = "slug"
    search_fields = ["name", "industry", "location"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        qs = selectors.companies(self.request.user)
        if self.request.query_params.get("mine") == "true":
            qs = qs.filter(members__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        company = services.create_company(self.request.user, **serializer.validated_data)
        serializer.instance = self.get_queryset().get(pk=company.pk)

    def perform_update(self, serializer):
        services.update_company(self.request.user, serializer.instance, **serializer.validated_data)
        serializer.instance = self.get_queryset().get(pk=serializer.instance.pk)

    def destroy(self, request, slug=None):
        company = self.get_object()
        services._require_team(request.user, company, admin=True)
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=None, responses=CompanySerializer)
    @action(detail=True, methods=["post", "delete"])
    def follow(self, request, slug=None):
        company = self.get_object()
        (services.follow if request.method == "POST" else services.unfollow)(request.user, company)
        return Response(self.get_serializer(self.get_queryset().get(pk=company.pk)).data)

    @extend_schema(methods=["GET"], responses=MemberSerializer(many=True))
    @extend_schema(methods=["POST"], request=AddMemberSerializer, responses=MemberSerializer)
    @action(detail=True, methods=["get", "post"], pagination_class=None)
    def members(self, request, slug=None):
        company = self.get_object()
        if request.method == "POST":
            data = AddMemberSerializer(data=request.data)
            data.is_valid(raise_exception=True)
            user = get_object_or_404(User, username=data.validated_data["username"])
            member = services.add_member(request.user, company, user, data.validated_data["role"])
            return Response(MemberSerializer(member).data, status=status.HTTP_201_CREATED)
        if selectors.role_in(request.user, company) is None:
            raise Http404
        return Response(
            MemberSerializer(company.members.select_related("user__profile"), many=True).data
        )


class CompanyMemberView(APIView):
    @extend_schema(responses={204: None})
    def delete(self, request, slug, user_id):
        company = get_object_or_404(Company, slug=slug)
        services.remove_member(request.user, company, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    parameters=[
        OpenApiParameter("company", OpenApiTypes.STR, description="A company slug"),
        OpenApiParameter("saved", OpenApiTypes.BOOL),
        OpenApiParameter("sort", OpenApiTypes.STR, enum=["newest", "match"]),
    ]
)
class JobViewSet(viewsets.ModelViewSet):
    """Open jobs; a company's team also sees its drafts and closed jobs."""

    serializer_class = JobSerializer
    filterset_fields = ["workplace", "employment_type", "level", "status"]
    search_fields = ["title", "description", "company__name", "location"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        qs = selectors.jobs(self.request.user)
        params = self.request.query_params
        if params.get("company"):
            qs = qs.filter(company__slug=params["company"])
        if params.get("saved") == "true":
            qs = qs.filter(saves__user=self.request.user)
        return qs

    def list(self, request):
        qs = self.filter_queryset(self.get_queryset())
        if request.query_params.get("sort") == "match":
            # shortcut: a ranked list is not cursor-paginated; capped at 100 rows.
            rows = qs.order_by("-matching_skills", "-published_at")[:100]
            return Response(
                {
                    "next": None,
                    "previous": None,
                    "results": self.get_serializer(rows, many=True).data,
                }
            )
        self.paginator.ordering = ["-published_at", "-created_at"]
        return super().list(request)

    def _fresh(self, job):
        return self.get_queryset().get(pk=job.pk)

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        slug = data.pop("company_slug", None)
        if not slug:
            raise ValidationError({"company_slug": "Say which company the job is at."})
        company = get_object_or_404(Company, slug=slug)
        job = services.create_job(self.request.user, company, skills=data.pop("skills", []), **data)
        serializer.instance = self._fresh(job)

    def perform_update(self, serializer):
        data = dict(serializer.validated_data)
        data.pop("company_slug", None)
        services.update_job(
            self.request.user, serializer.instance, skills=data.pop("skills", None), **data
        )
        serializer.instance = self._fresh(serializer.instance)

    def perform_destroy(self, instance):
        services.delete_job(self.request.user, instance)

    @extend_schema(request=None, responses=JobSerializer)
    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        return Response(
            self.get_serializer(
                self._fresh(services.publish_job(request.user, self.get_object()))
            ).data
        )

    @extend_schema(request=None, responses=JobSerializer)
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        return Response(
            self.get_serializer(
                self._fresh(services.close_job(request.user, self.get_object()))
            ).data
        )

    @extend_schema(request=None, responses=JobSerializer)
    @action(detail=True, methods=["post", "delete"])
    def save(self, request, pk=None):
        job = self.get_object()
        (services.save_job if request.method == "POST" else services.unsave_job)(request.user, job)
        return Response(self.get_serializer(self._fresh(job)).data)

    @extend_schema(
        request={"multipart/form-data": ApplySerializer}, responses={201: ApplicationSerializer}
    )
    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def apply(self, request, pk=None):
        data = ApplySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        application = services.apply(
            request.user,
            self.get_object(),
            data.validated_data["resume"],
            data.validated_data.get("cover_letter", ""),
        )
        return Response(
            ApplicationSerializer(application, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=ApplicationSerializer(many=True))
    @action(detail=True, methods=["get"])
    def applications(self, request, pk=None):
        job = self.get_object()
        services._require_team(request.user, job.company)
        page = self.paginate_queryset(selectors.applications(request.user).filter(job=job))
        return self.get_paginated_response(
            ApplicationSerializer(page, many=True, context={"request": request}).data
        )


class ApplicationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /applications/ lists your own. The hiring team reads them through the job."""

    serializer_class = ApplicationSerializer

    def get_queryset(self):
        qs = selectors.applications(self.request.user)
        return qs.filter(applicant=self.request.user) if self.action == "list" else qs

    @extend_schema(request=StatusSerializer, responses=ApplicationSerializer)
    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        data = StatusSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        application = services.set_status(
            request.user, self.get_object(), data.validated_data["status"]
        )
        return Response(self.get_serializer(application).data)

    @extend_schema(request=None, responses=ApplicationSerializer)
    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        return Response(
            self.get_serializer(services.withdraw(request.user, self.get_object())).data
        )

    @extend_schema(responses={(200, "application/pdf"): OpenApiTypes.BINARY})
    @action(detail=True, methods=["get"], url_path="resume", url_name="resume")
    def resume(self, request, pk=None):
        application = self.get_object()
        return FileResponse(
            application.resume.open("rb"),
            content_type="application/pdf",
            as_attachment=False,
            filename=f"resume-{application.applicant.username}.pdf",
        )
