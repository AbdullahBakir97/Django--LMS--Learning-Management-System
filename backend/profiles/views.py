from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Education, Experience, ProfileSkill, Skill
from .selectors import profile_queryset
from .serializers import (
    AddSkillSerializer,
    EducationSerializer,
    ExperienceSerializer,
    ProfileSerializer,
    ProfileSkillSerializer,
    SkillSerializer,
)


class MyProfileView(generics.RetrieveUpdateAPIView):
    """GET or PATCH the signed-in user's profile."""

    serializer_class = ProfileSerializer

    def get_object(self):
        return profile_queryset().get(user=self.request.user)


class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    queryset = profile_queryset()
    lookup_field = "user__username"
    lookup_url_kwarg = "username"


class OwnEntriesViewSet(viewsets.ModelViewSet):
    """CRUD on entries that belong to the signed-in user's profile."""

    pagination_class = None

    def get_queryset(self):
        return self.queryset.filter(profile__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class ExperienceViewSet(OwnEntriesViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer


class EducationViewSet(OwnEntriesViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer


class ProfileSkillViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = ProfileSkillSerializer
    pagination_class = None

    def get_queryset(self):
        return profile_queryset().get(user=self.request.user).skills.all()

    @extend_schema(request=AddSkillSerializer, responses={201: ProfileSkillSerializer})
    def create(self, request):
        data = AddSkillSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        profile_skill = services.add_skill(request.user.profile, **data.validated_data)
        profile_skill.endorsement_count = 0
        return Response(ProfileSkillSerializer(profile_skill).data, status=status.HTTP_201_CREATED)


class EndorseView(APIView):
    """POST to endorse someone's skill, DELETE to withdraw."""

    def _skill(self, username, pk):
        return get_object_or_404(
            ProfileSkill.objects.select_related("profile"), pk=pk, profile__user__username=username
        )

    @extend_schema(request=None, responses={201: None})
    def post(self, request, username, pk):
        services.endorse(request.user, self._skill(username, pk))
        return Response(status=status.HTTP_201_CREATED)

    @extend_schema(responses={204: None})
    def delete(self, request, username, pk):
        services.withdraw_endorsement(request.user, self._skill(username, pk))
        return Response(status=status.HTTP_204_NO_CONTENT)


class SkillSearchView(generics.ListAPIView):
    """Taxonomy lookup for autocomplete: /api/skills/?search=py"""

    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    pagination_class = None

    def get_queryset(self):
        return super().get_queryset()[:20]
