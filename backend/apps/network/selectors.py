from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from apps.profiles.models import ProfileSkill

from .models import Connection, Follow, Recommendation

User = get_user_model()
Status = Connection.Status


def people():
    return User.objects.filter(is_active=True).select_related("profile")


def connection_between(a, b) -> Connection | None:
    return Connection.objects.filter(
        Q(requester=a, addressee=b) | Q(requester=b, addressee=a)
    ).first()


def connections_of(user):
    return connections_of_id(user.id).select_related("requester__profile", "addressee__profile")


def connections_of_id(user_id: int):
    return Connection.objects.filter(
        Q(requester_id=user_id) | Q(addressee_id=user_id), status=Status.ACCEPTED
    )


def requests_for(user, direction: str):
    field = "addressee" if direction == "incoming" else "requester"
    return Connection.objects.filter(**{field: user}, status=Status.PENDING).select_related(
        "requester__profile", "addressee__profile"
    )


def relationship(viewer, other) -> dict:
    connection = connection_between(viewer, other)
    return {
        "following": Follow.objects.filter(follower=viewer, following=other).exists(),
        "followed_by": Follow.objects.filter(follower=other, following=viewer).exists(),
        "followers": Follow.objects.filter(following=other).count(),
        "following_count": Follow.objects.filter(follower=other).count(),
        "connections": connections_of(other).count(),
        "connection": None
        if connection is None
        else {
            "id": connection.id,
            "status": connection.status,
            "direction": "outgoing" if connection.requester_id == viewer.id else "incoming",
        },
    }


def suggestions_for(user, limit: int = 10):
    """People who share your skills, most shared first, excluding anyone you are linked to."""
    my_skills = ProfileSkill.objects.filter(profile__user=user).values("skill_id")
    linked = Connection.objects.filter(Q(requester=user) | Q(addressee=user)).values_list(
        "requester_id", "addressee_id"
    )
    exclude = {user.id} | {uid for pair in linked for uid in pair}
    return (
        people()
        .exclude(id__in=exclude)
        .annotate(
            shared_skills=Count(
                "profile__skills", filter=Q(profile__skills__skill_id__in=my_skills), distinct=True
            )
        )
        .filter(shared_skills__gt=0)
        .order_by("-shared_skills", "username")[:limit]
    )


def recommendations_for(viewer, recipient):
    """Published ones for everyone; the recipient also sees pending and hidden ones to decide."""
    rows = Recommendation.objects.filter(recipient=recipient).select_related("author__profile")
    if viewer.id != recipient.id:
        rows = rows.filter(status=Recommendation.Status.PUBLISHED)
    return rows
