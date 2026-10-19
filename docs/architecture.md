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

## Offline reading

`frontend/public/sw.js` is a small service worker, registered only in production builds. It keeps three caches:

- **App shell.** Pages are fetched from the network first and fall back to the cached `index.html`, so every route opens offline.
- **Assets.** Files under `/assets/` carry a content hash in their names, so they are served from the cache first.
- **Course reading.** `GET` requests for `/api/auth/user/`, `/api/me/enrollments/` and `/api/courses/…` go to the network first; offline, the last copy is used. No other API response is stored.

The session store uses the cached user only when the browser reports it is offline and the refresh cookie cannot be used. Writes still need the network. Signing out posts `sign-out` to the worker, which deletes the course-reading cache. To retire old caches, bump `VERSION` in `sw.js`.

## Search

`apps/search` is the one context above all the others. It has no models. For each kind of result, it calls the owning context's visibility selector, such as `visible_courses`, `events_visible` or `jobs`, and ranks rows with PostgreSQL full-text search. This keeps every visibility rule in one place. A new searchable kind needs a finder in `selectors.py` and a row shape in `serializers.py`.

Search vectors are computed per query, which is fast enough at this size. When a search starts taking more than about 100 ms, store a `SearchVectorField` with a GIN index on the large tables.

## Overview

`apps/insights` is read-only and has no models. It sits at the top with search, and counts across every context for the admin overview. Weekly series come from `core.stats.weekly_counts`, which course analytics also uses. The counts run per request. When the overview gets slow, cache it for a few minutes, because nobody needs it to the second.

## Payments

`apps/payments` sits above learning and calls it, never the other way round. `learning.services.enroll` refuses a paid course with `402 Payment Required`. `payments.start_checkout` runs the same enrolment checks, records a pending `Order` that copies the price, and opens a Stripe Checkout session tied to it. The webhook verifies Stripe's signature, then in one transaction locks the order, checks the amount and currency, marks it paid and calls `enroll(..., paid=True)`. A repeated delivery finds the order already paid and does nothing. The order keeps the list price and what was paid, which is lower when a promotion code was used. The subtotal must match the list price. A full `charge.refunded` marks the order refunded and calls `learning.unenroll`. Revenue counts paid orders only, so a refund comes off the totals. The success page in the app only polls progress. Coming back from Stripe unlocks nothing by itself.
