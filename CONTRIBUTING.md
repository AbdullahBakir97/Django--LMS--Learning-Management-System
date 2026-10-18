# Contributing

Thanks for helping build the LMS. This page is the short version; the design rules the code
follows are in [docs/architecture.md](docs/architecture.md).

## Set up

```bash
cp .env.example .env            # set DJANGO_SECRET_KEY
make dev                        # postgres, redis, backend, worker
make migrate
pre-commit install              # ruff on every commit
```

## Make a change

1. Branch from `main`: `feat/<topic>`, `fix/<topic>` or `chore/<topic>`.
2. Keep the change inside one context (`backend/apps/<context>/`) unless it is kernel work in
   `backend/apps/core/`. A context imports only from layers below it (see the domain map).
3. Add or update tests next to the code (`backend/apps/<context>/tests/`). Factories live in
   `backend/conftest.py`.
4. Run `make lint` and `make test`. CI runs the same checks against PostgreSQL and Redis.
5. Open a pull request using the template. Describe what changed and how to verify it.

## Conventions

- Identity comes from `request.user`; never from an id in the URL or body.
- Writes go through `services.py`, reads through `selectors.py`.
- Database constraints for every invariant (unique, check, index).
- Cross-context side effects are domain events (`core.events`), published on commit.
- Commit messages: `type: short summary` (`feat`, `fix`, `chore`, `docs`, `test`, `refactor`).

## Reporting problems

Bugs and feature requests go through the issue templates. Security issues go through
[SECURITY.md](SECURITY.md), not public issues.
