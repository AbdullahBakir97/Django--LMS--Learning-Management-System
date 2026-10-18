"""One search across contexts. This app sits above every other one: it reads their visibility
selectors, so a private group's posts, a draft course or another team's draft job never leak.

shortcut: vectors are computed per query, fine for tens of thousands of rows; store a
SearchVectorField with a GIN index per model when a search takes longer than ~100 ms.
"""

import re

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F

from apps.careers import selectors as careers
from apps.careers.models import Job
from apps.community import selectors as community
from apps.learning import selectors as learning
from apps.network import selectors as network

CONFIG = "simple"  # no stemming: works the same for every language a white-label install uses
KINDS = ("people", "courses", "groups", "events", "jobs", "companies")


def query_for(text: str) -> SearchQuery | None:
    """Every word must match, the last one as a prefix, so results appear while typing."""
    words = re.findall(r"\w+", text.lower())[:6]
    if not words:
        return None
    terms = [*words[:-1], f"{words[-1]}:*"]
    return SearchQuery(" & ".join(terms), search_type="raw", config=CONFIG)


def _ranked(qs, query, *weighted):
    vector = SearchVector(*weighted[0][1:], weight=weighted[0][0], config=CONFIG)
    for weight, *fields in weighted[1:]:
        vector = vector + SearchVector(*fields, weight=weight, config=CONFIG)
    return (
        qs.annotate(rank=SearchRank(vector, query), match=vector)
        .filter(match=query)
        .order_by(F("rank").desc())
    )


def _people(user, q):
    return _ranked(
        network.people(),
        q,
        ("A", "first_name", "last_name", "username"),
        ("B", "profile__headline"),
    )


def _courses(user, q):
    return _ranked(
        learning.visible_courses(user), q, ("A", "title"), ("B", "summary", "description")
    )


def _groups(user, q):
    return _ranked(community.groups_visible(user), q, ("A", "name"), ("B", "description"))


def _events(user, q):
    return _ranked(
        community.events_visible(user), q, ("A", "title"), ("B", "description", "location")
    )


def _jobs(user, q):
    open_jobs = careers.jobs(user).filter(status=Job.Status.OPEN)
    return _ranked(open_jobs, q, ("A", "title"), ("B", "company__name", "location", "description"))


def _companies(user, q):
    return _ranked(
        careers.companies(user), q, ("A", "name"), ("B", "industry", "location", "description")
    )


FINDERS = {
    "people": _people,
    "courses": _courses,
    "groups": _groups,
    "events": _events,
    "jobs": _jobs,
    "companies": _companies,
}


def search(user, text: str, kinds=KINDS, limit: int = 5) -> dict[str, list]:
    query = query_for(text)
    if query is None:
        return {kind: [] for kind in kinds}
    return {kind: list(FINDERS[kind](user, query)[:limit]) for kind in kinds}
