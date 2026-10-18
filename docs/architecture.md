# Architecture

Two views of the system, then the rules the code follows. The diagrams are maintained as
self-contained HTML (`docs/diagrams/*.html`); the PNGs are renders of the same files.

## System

![System architecture](diagrams/system-architecture.png)

The SPA talks REST for data and holds one WebSocket for live updates. Nginx terminates TLS,
serves the built SPA and proxies `/api` and `/ws` to the ASGI server. Every write lands in
PostgreSQL. Services publish domain events after commit; the realtime gateway fans them out
through Redis to the users concerned. Slow work (mail, PDF certificates, digests) runs in Celery
workers off the same Redis.

## Domain

![Domain layers](diagrams/domain-layers.png)

Nine bounded contexts in five layers. **A context imports only from the layers below it.**
Anything that must travel upward is a domain event the kernel delivers.

| Layer | Contexts | Owns |
|---|---|---|
| L5 Product | learning, community (groups, posts, events), career, messaging | what users come for |
| L4 Social fabric | network, engagement, notifications | follow and connect, reactions and comments, delivery |
| L3 Identity | accounts, profiles | user, roles, profile, skills |
| L2 Platform kernel | core | permissions, pagination, errors, events, realtime, logging |
| L1 Infrastructure | PostgreSQL, Redis, object storage, Celery, SMTP | swappable by settings |

## Inside a context

```
backend/apps/learning/
  models.py        schema, constraints, indexes, ordering
  selectors.py     reads: querysets, filters, select_related, annotations
  services.py      writes: plain functions that take the acting user and raise domain errors
  serializers.py   validation in, shaped output out
  views.py         DRF ViewSets, permission classes, OpenAPI annotations
  urls.py          a router
  permissions.py   IsInstructor, IsEnrolled, ...
  events.py        the events this context publishes
  tasks.py         Celery tasks
  tests/           factories, test_models, test_services, test_api
```

## Rules

- Identity comes from the session. Services receive the acting user; views pass `request.user`.
  No user id in a URL or body decides who acts.
- Services own writes, selectors own reads. Views never mutate through the ORM directly.
- Constraints live in the database: unique, check and index declarations on every model.
- Cross-context side effects go through `core.events`, published in `transaction.on_commit`.
- One notification write path, one realtime group per user (`user.<id>`), one task queue.
- The WebSocket authenticates with a signed ticket from `POST /api/realtime/ticket/` that lives
  30 seconds, so the bearer token never appears in a URL. Pushes are best effort; the list API is
  the source of truth.
- API: resource nouns, nested where ownership is natural, cursor pagination, django-filter,
  OpenAPI from drf-spectacular, errors as RFC 9457 problem documents.
- Configuration from the environment. The same image runs locally, in CI and in production.

## Engagement targets

Comments and reactions live in `engagement` (L4), but what they attach to lives above it. A
product context registers its models from `AppConfig.ready()`:

```python
registry.register("lesson", Lesson, can_view=..., owner_id=..., url=..., title=...)
```

The API addresses targets as `/api/engagement/<key>/<id>/comments/` and `.../reactions/`. The
registry decides visibility (a gated lesson's discussion is a 404 to someone who cannot open the
lesson), who may moderate (the owner), and what a notification links to.

## Messages up the socket

The WebSocket is mostly a push channel, but the SPA can send small hints up it (today only
`{"type": "typing", "conversation": id}`). Core does not know about messaging, so a context
registers a handler from `AppConfig.ready()`:

```python
@on_client_message("typing")
def typing(user, payload): ...
```

Handlers run with database access, check membership themselves, and never write. Malformed
frames are dropped without closing the connection.
