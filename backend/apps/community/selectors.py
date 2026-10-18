from django.db.models import Count, OuterRef, Q

from apps.network.models import Connection, Follow

from .models import Attendance, Event, Group, Membership, Post

Active = Membership.Status.ACTIVE


def membership(user, group) -> Membership | None:
    return Membership.objects.filter(user=user, group=group).first()


def is_member(user, group) -> bool:
    return Membership.objects.filter(user=user, group=group, status=Active).exists()


def groups_visible(user):
    """All groups are listed (private ones show their name and description, not their posts)."""
    mine = Membership.objects.filter(group=OuterRef("pk"), user=user)
    return Group.objects.select_related("owner").annotate(
        member_count=Count("memberships", filter=Q(memberships__status=Active), distinct=True),
        my_status=mine.values("status")[:1],
        my_role=mine.values("role")[:1],
    )


def can_see_group_content(user, group) -> bool:
    return group.privacy == Group.Privacy.PUBLIC or is_member(user, group)


def can_view_post(user, post) -> bool:
    return post.group_id is None or can_see_group_content(user, post.group)


def readable_groups(user):
    return Group.objects.filter(
        Q(privacy=Group.Privacy.PUBLIC) | Q(memberships__user=user, memberships__status=Active)
    ).values("pk")


def posts_base():
    return Post.objects.select_related("author__profile", "group")


def feed_for(user):
    """Your posts, posts by people you follow or are connected with, and posts in your groups."""
    followed = Follow.objects.filter(follower=user).values("following_id")
    connected = Connection.objects.filter(
        Q(requester=user) | Q(addressee=user), status=Connection.Status.ACCEPTED
    ).values_list("requester_id", "addressee_id")
    people = {user.id} | {uid for pair in connected for uid in pair}
    my_groups = Membership.objects.filter(user=user, status=Active).values("group_id")
    return posts_base().filter(
        (Q(author_id__in=people) | Q(author_id__in=followed)) & Q(group__isnull=True)
        | Q(group_id__in=my_groups)
    )


def posts_in(group):
    return posts_base().filter(group=group)


def posts_by(author, viewer):
    return (
        posts_base()
        .filter(author=author)
        .filter(Q(group__isnull=True) | Q(group_id__in=readable_groups(viewer)))
    )


def events_visible(user):
    going = Attendance.objects.filter(event=OuterRef("pk"), user=user)
    return (
        Event.objects.filter(Q(group__isnull=True) | Q(group_id__in=readable_groups(user)))
        .select_related("host", "group")
        .annotate(
            going_count=Count(
                "attendances", filter=Q(attendances__status=Attendance.Status.GOING), distinct=True
            ),
            my_status=going.values("status")[:1],
        )
    )
