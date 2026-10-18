"""Writes with rules. Plain CRUD on a profile's own entries needs no service."""

from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events

from . import events as names
from .models import Endorsement, Profile, ProfileSkill, Skill


def add_skill(profile: Profile, name: str, level: str) -> ProfileSkill:
    skill, _ = Skill.objects.get_or_create(
        name__iexact=name.strip(), defaults={"name": name.strip()}
    )
    if ProfileSkill.objects.filter(profile=profile, skill=skill).exists():
        raise ValidationError({"name": "This skill is already on the profile."})
    return ProfileSkill.objects.create(profile=profile, skill=skill, level=level)


def endorse(actor, profile_skill: ProfileSkill) -> Endorsement:
    if profile_skill.profile.user_id == actor.id:
        raise PermissionDenied("You cannot endorse your own skill.")
    endorsement, created = Endorsement.objects.get_or_create(
        profile_skill=profile_skill, endorsed_by=actor
    )
    if created:
        events.publish(
            names.SKILL_ENDORSED,
            recipient_id=profile_skill.profile.user_id,
            actor_id=actor.id,
            actor_name=actor.get_full_name() or actor.username,
            skill_name=profile_skill.skill.name,
        )
    return endorsement


def withdraw_endorsement(actor, profile_skill: ProfileSkill) -> None:
    Endorsement.objects.filter(profile_skill=profile_skill, endorsed_by=actor).delete()
