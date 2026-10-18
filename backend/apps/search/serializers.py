from rest_framework import serializers


class HitSerializer(serializers.Serializer):
    """One result, whatever its kind: enough to draw a row and link to the page."""

    kind = serializers.CharField()
    id = serializers.IntegerField()
    title = serializers.CharField()
    subtitle = serializers.CharField(allow_blank=True)
    url = serializers.CharField()
    image = serializers.CharField(allow_null=True)


def _image(field) -> str | None:
    return field.url if field else None


def _when(moment) -> str:
    return moment.strftime("%d %b %Y")


HIT = {
    "people": lambda u: {
        "id": u.id,
        "title": u.get_full_name() or u.username,
        "subtitle": u.profile.headline or f"@{u.username}",
        "url": f"/u/{u.username}",
        "image": _image(u.profile.avatar),
    },
    "courses": lambda c: {
        "id": c.id,
        "title": c.title,
        "subtitle": c.summary or c.get_level_display(),
        "url": f"/courses/{c.slug}",
        "image": _image(c.cover),
    },
    "groups": lambda g: {
        "id": g.id,
        "title": g.name,
        "subtitle": f"{g.get_privacy_display()} group · {g.member_count} members",
        "url": f"/groups/{g.slug}",
        "image": None,
    },
    "events": lambda e: {
        "id": e.id,
        "title": e.title,
        "subtitle": " · ".join(filter(None, [_when(e.starts_at), e.location])),
        "url": f"/events/{e.id}",
        "image": None,
    },
    "jobs": lambda j: {
        "id": j.id,
        "title": j.title,
        "subtitle": " · ".join(filter(None, [j.company.name, j.location])),
        "url": f"/jobs/{j.id}",
        "image": _image(j.company.logo),
    },
    "companies": lambda c: {
        "id": c.id,
        "title": c.name,
        "subtitle": " · ".join(filter(None, [c.industry, c.location])),
        "url": f"/companies/{c.slug}",
        "image": _image(c.logo),
    },
}


def hits(kind: str, rows) -> list[dict]:
    return [{"kind": kind, **HIT[kind](row)} for row in rows]
