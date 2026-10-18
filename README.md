# Django LMS

A learning management system and professional network: courses with lessons, quizzes and
certificates; profiles, connections and groups; jobs and companies; messaging and notifications.
Django and Django REST Framework on PostgreSQL and Redis, with a Vue 3 frontend (in progress).

[![CI](https://github.com/AbdullahBakir97/Django--LMS--Learning-Management-System/actions/workflows/ci.yml/badge.svg)](https://github.com/AbdullahBakir97/Django--LMS--Learning-Management-System/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

![System architecture](docs/diagrams/system-architecture.png)

The full design, the domain map and the rules the code follows are in
[docs/architecture.md](docs/architecture.md).

## Status

The project is being rebuilt in phases, one pull request each. Phase 1 (this foundation) gives
you a backend that boots, migrates, serves its OpenAPI schema and passes CI. Feature contexts
land in the following phases.

## Repository layout

| Path | What it is |
|---|---|
| `backend/` | Django project: `config/` (settings, ASGI, Celery), `apps/core/` (kernel), `apps/<context>/` per bounded context |
| `docs/` | Architecture, diagrams, decisions |
| `docker-compose.yml` | PostgreSQL, Redis, backend and worker for local development |

## Getting started

Requirements: Docker with Compose, or Python 3.12 with PostgreSQL 16 and Redis 7 running locally.

```bash
cp .env.example .env            # set DJANGO_SECRET_KEY
make dev                        # builds and starts postgres, redis, backend, worker
make migrate
docker compose exec backend python manage.py createsuperuser
```

Then open <http://localhost:8000/api/docs/> for the API and <http://localhost:8000/admin/>.

Without Docker:

```bash
cd backend
pip install -r requirements-dev.txt
export $(grep -v '^#' ../.env | xargs)
python manage.py migrate && python manage.py runserver
```

| Command | Does |
|---|---|
| `make test` | pytest against the test settings |
| `make lint` / `make fmt` | ruff check and format |
| `pre-commit install` | run the same checks before each commit |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/architecture.md](docs/architecture.md) first.
Security issues go through [SECURITY.md](SECURITY.md). Licensed under the [MIT License](LICENSE).
