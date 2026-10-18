from django.db.models import Count, Prefetch

from .models import Profile, ProfileSkill


def profile_queryset():
    skills = ProfileSkill.objects.select_related("skill").annotate(
        endorsement_count=Count("endorsements")
    )
    return Profile.objects.select_related("user").prefetch_related(
        "experiences", "educations", Prefetch("skills", queryset=skills)
    )
