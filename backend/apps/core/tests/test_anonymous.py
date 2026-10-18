"""Every API route answers an anonymous caller with a client error, never a server error."""

import re
import uuid

import pytest
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.test import APIClient

SAMPLE = {"int": "1", "slug": "x", "str": "x", "uuid": str(uuid.uuid4()), "path": "x"}
PUBLIC = {"api/health/", "api/schema/", "api/docs/"}


def routes(resolver=None, prefix=""):
    for p in (resolver or get_resolver()).url_patterns:
        pattern = prefix + str(p.pattern)
        if isinstance(p, URLResolver):
            yield from routes(p, pattern)
        elif isinstance(p, URLPattern) and pattern.startswith("api/"):
            yield p, pattern


def concrete(p: URLPattern, pattern: str) -> str | None:
    if "format" in pattern:  # router format-suffix variants duplicate the plain routes
        return None
    path = pattern
    for name, conv in getattr(p.pattern, "converters", {}).items():
        kind = type(conv).__name__.replace("Converter", "").lower()
        path = path.replace(f"<{kind}:{name}>", SAMPLE.get(kind, "1")).replace(f"<{name}>", "x")
    # Router regexes: ^courses/(?P<slug>[^/.]+)/publish/$
    path = re.sub(
        r"\(\?P<(\w+)>[^)]*\)", lambda m: "1" if m.group(1) in ("pk", "id") else "x", path
    )
    path = path.replace("^", "").replace("$", "")
    if "<" in path or "(" in path:
        return None
    return "/" + path


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post"])
def test_no_server_errors_for_anonymous_callers(method):
    client = APIClient(raise_request_exception=False)
    checked = 0
    for p, pattern in routes():
        path = concrete(p, pattern)
        if not path or path.strip("/") + "/" in PUBLIC:
            continue
        status = getattr(client, method)(path).status_code
        assert status < 500, f"{method.upper()} {path} -> {status}"
        checked += 1
    assert checked > 40
