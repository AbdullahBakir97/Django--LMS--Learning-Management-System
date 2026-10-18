# Django LMS

A learning platform and professional network in one: courses with quizzes and verifiable
certificates, a feed and groups, events, jobs with private applications, live messaging and
notifications. Django REST Framework on PostgreSQL and Redis, with a Vue 3 frontend.

[![CI](https://github.com/AbdullahBakir97/Django--LMS--Learning-Management-System/actions/workflows/ci.yml/badge.svg)](https://github.com/AbdullahBakir97/Django--LMS--Learning-Management-System/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

![The home feed](docs/screenshots/feed-light.png)

## What it does

| Area | For learners | For instructors, organisers and employers |
|---|---|---|
| **Learning** | Catalogue of free and paid courses, card payment through Stripe Checkout, enrolment with prerequisites, lessons in markdown with video, quizzes, progress, a PDF certificate anyone can verify; installable on a phone, and lessons you opened stay readable offline | Course editor, lessons, quiz builder, publishing, pricing, course analytics: enrolments per week, where learners stop, quiz results, stalled learners |
| **Discussion** | Comments, replies and reactions on lessons and posts | Moderation of discussions on your own lessons and groups |
| **Profiles** | Experience, education, skills and endorsements, a portfolio, badges earned along the way, recommendations from connections that you approve | |
| **Network** | Follow, connect, people who share your skills | |
| **Community** | A feed with images and shares, public and private groups, events with RSVPs and ratings afterwards | Group roles and approvals, events with capacity, attendee feedback |
| **Careers** | Job search with skill match, saved jobs, applications with a private résumé, interview invitations to confirm and add to a calendar | Company pages, job posts, an applicant pipeline, interview scheduling, company updates for followers |
| **Messaging** | Direct and group conversations, live, with typing and read receipts | |
| **Search** | One box for people, courses, groups, events, jobs and companies, with results as you type (Ctrl/⌘ K) | Drafts and private groups stay visible only to the people who can see them |
| **Safety** | Report a post, a comment or a person; hear back when a moderator has looked | A moderation queue that groups reports by item, with remove, deactivate or dismiss |
| **Notifications** | Live in the app, email for what matters or a daily or weekly digest, quiet hours in your time zone, per-kind preferences | |

Accounts use email sign-in with verification and password reset. Every list is cursor-paged,
every error is an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem document, and the
API is described by OpenAPI at `/api/docs/`.

## Screenshots

| | |
|---|---|
| ![Lesson with discussion](docs/screenshots/discussion-dark.png) | ![Messages](docs/screenshots/messages-light.png) |
| Lesson player and its discussion | Live messaging |
| ![Jobs](docs/screenshots/jobs-light.png) | ![Applicants](docs/screenshots/applicants-light.png) |
| Jobs matched to your skills | The hiring team's applicant view |
| ![Group](docs/screenshots/group-members-light.png) | ![Network](docs/screenshots/network-light.png) |
| Group members and requests | Network and suggestions |
| ![Profile](docs/screenshots/profile-light.png) | ![Interviews](docs/screenshots/interviews-light.png) |
| A profile with portfolio, badges and recommendations | Interview invitations to confirm |
| ![Offline](docs/screenshots/offline-mobile.png) | ![Search](docs/screenshots/search-light.png) |
| A lesson read offline on a phone | Search across everything as you type |
| ![Posts](docs/screenshots/posts-light.png) | ![Moderation](docs/screenshots/moderation-light.png) |
| The feed with images, a share and company news | The moderation queue |
| ![Analytics](docs/screenshots/analytics-light.png) | ![Buy a course](docs/screenshots/buy-light.png) |
| Course analytics for its instructor | A paid course, with a free preview lesson |

Light and dark themes, and every screen works at phone width. More in
[docs/screenshots](docs/screenshots).

## Architecture

![System architecture](docs/diagrams/system-architecture.png)

Nine bounded contexts in five layers, each importing only from the layers below. Anything that
needs to travel upward is a domain event published after commit. The design, the rules and the
reasons are in [docs/architecture.md](docs/architecture.md).

![Domain layers](docs/diagrams/domain-layers.png)

### Codebase map

Generated from the code graph (graphify; tests, migrations and admin modules left out): arrows
point from a module to what it uses, and the number is how many links the graph found. Dotted
arrows are domain events: `notifications` hears about enrolments, follows and comments without
importing the contexts that publish them.

```mermaid
flowchart LR
  subgraph Backend
    config --> accounts & careers & community & engagement & learning & messaging & network & notifications & profiles & core
    notifications -- 31 --> core
    profiles -- 20 --> core
    careers -- 18 --> core
    learning -- 18 --> core
    community -- 16 --> engagement
    community -- 15 --> core
    network -- 13 --> core
    messaging -- 11 --> core
    engagement -- 10 --> core
    careers -- 6 --> profiles
    careers -- 5 --> engagement
    community -- 5 --> network
    messaging -- 5 --> engagement
    learning -- 4 --> accounts
    profiles -- 3 --> accounts
    messaging -- 3 --> network
    network -- 3 --> profiles
    accounts -- 2 --> core
    learning -- 2 --> engagement
    learning -. events .-> notifications
    profiles -. events .-> notifications
    network -. events .-> notifications
    engagement -. events .-> notifications
    community -. events .-> notifications
    careers -. events .-> notifications
    messaging -. events .-> notifications
  end
  subgraph Frontend
    pages -- 169 --> api
    features -- 158 --> api
    pages -- 99 --> components
    pages -- 74 --> features
    router -- 66 --> pages
    features -- 54 --> components
    pages -- 22 --> stores
    features -- 17 --> stores
    stores -- 14 --> api
  end
  api -. REST and WebSocket .-> config
```

The full graph (every module, class and function, with an Obsidian vault and canvas) is
regenerated locally with `graphify backend frontend --obsidian`; it is not committed.

## Getting started

Requirements: Docker with Compose. (Or Python 3.12, Node 22 with pnpm, PostgreSQL 16 and Redis 7.)

```bash
cp .env.example .env            # set DJANGO_SECRET_KEY
make dev                        # postgres, redis, backend, worker and the app with hot reload
make migrate
make seed                       # demo people, courses, groups, events, jobs and conversations
```

Open <http://localhost:5173>. The demo accounts are `karim`, `amina` (instructors), `lina`,
`omar`, `sara` (who moderates), `yusuf` and `rana` (who hires for Nahla Labs), each as `<name>@demo.lms`. They
share one password: `make seed` prints it, or set `DEMO_PASSWORD` in `.env` to choose it. The API
docs are at <http://localhost:8000/api/docs/>.

| Command | Does |
|---|---|
| `make test` | backend pytest and frontend unit tests |
| `make e2e` | Playwright journeys (search, posting a photo, moderation, analytics) against the seeded dev stack |
| `make lint` / `make fmt` | ruff, ESLint, Prettier and vue-tsc |
| `make schema` | write the OpenAPI schema, failing on any warning |
| `make help` | every target |

## Production

Two images: the API (also used for the Celery worker and migrations) and nginx serving the app.
`make prod-up` runs the whole stack from `docker-compose.prod.yml`; pushing a `v*` tag publishes
versioned images to the GitHub Container Registry. Settings, TLS, backups and the checklist are
in [docs/deployment.md](docs/deployment.md).

## Repository layout

| Path | What it is |
|---|---|
| `backend/` | Django project: `config/` (settings, ASGI, Celery), `apps/core/` (kernel), `apps/<context>/` per bounded context |
| `frontend/` | Vue 3 app: `src/api` (typed client), `src/stores`, `src/lib` (live connection), `src/components/ui`, `src/features`, `src/pages` |
| `DESIGN.md`, `PRODUCT.md` | The visual system and the product brief the frontend follows |
| `docs/` | Architecture, deployment, diagrams, screenshots |
| `docker-compose.yml`, `docker-compose.prod.yml` | Local development, and a production-like stack |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/architecture.md](docs/architecture.md) first.
Changes are listed in [CHANGELOG.md](CHANGELOG.md). Security issues go through
[SECURITY.md](SECURITY.md). Licensed under the [MIT License](LICENSE).
