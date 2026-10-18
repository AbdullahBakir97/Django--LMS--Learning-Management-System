# Deployment

The production stack is two images and four supporting services, described in
`docker-compose.prod.yml`:

| Service | Image | Role |
|---|---|---|
| `web` | `frontend/Dockerfile` | nginx: serves the built app, proxies `/api`, `/ws`, `/admin`, `/static` to the backend, serves public media |
| `backend` | `backend/Dockerfile` | the ASGI app (uvicorn, two workers): REST, WebSockets, admin, static files through WhiteNoise |
| `worker` | `backend/Dockerfile` | Celery: certificate PDFs and email |
| `beat` | `backend/Dockerfile` | the Celery scheduler: sends notification digests every hour, exactly one instance |
| `migrate` | `backend/Dockerfile` | runs migrations once, before `backend` and `worker` start |
| `postgres`, `redis` | official images | data; cache, channel layer and task broker |

## First run

```bash
cp .env.production.example .env.production   # fill in every empty value
make prod-up                                  # builds, migrates, starts
docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec backend python manage.py createsuperuser
```

`web` listens on `WEB_PORT` (80 by default) and speaks plain HTTP. Put TLS in front of it: a cloud
load balancer, Caddy or Traefik. The terminator must send `X-Forwarded-Proto: https`; nginx passes
it through, and Django uses it for secure cookies and the HTTPS redirect.

## Settings

Everything comes from the environment. The ones that matter most:

| Variable | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | long and random; rotating it signs everyone out |
| `DJANGO_ALLOWED_HOSTS` | your domain; also used to check the origin of WebSocket connections |
| `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL` | `https://` plus your domain |
| `POSTGRES_PASSWORD` | long and random |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | SMTP for verification, password reset and notification email |
| `THROTTLE_ANON`, `THROTTLE_USER`, `THROTTLE_AUTH` | rate limits, defaults 60, 600 and 10 per minute |

## What production settings enforce

- HTTPS redirect (except the health check, which probes call over plain HTTP), HSTS with preload,
  secure and HttpOnly cookies, `nosniff`, `same-origin` referrers, frames denied.
- The refresh token lives in an HttpOnly cookie scoped to the refresh endpoint. The access token is
  kept in memory by the app and sent as a bearer header.
- The WebSocket authenticates with a signed ticket that lives 30 seconds, never a token in the URL.
- Rate limits per client on sign-in, sign-up and password reset, and per user everywhere else.
- nginx sends a Content Security Policy that allows scripts only from the site itself.
- Résumés are never served by nginx (`/media/resumes/` is a 404). The API streams them after
  checking that the caller is the applicant or on the hiring team.

CI runs `manage.py check --deploy --fail-level WARNING` against these settings on every push.

## Health and logs

- `GET /api/health/` returns `{"status": "ok", "database": true, "cache": true}`. The backend image
  has a Docker health check on it; the worker's checks Celery with `inspect ping`.
- Logs are JSON lines on stdout, one object per event, ready for any collector.

## Backups

Back up the `pgdata` and `media` volumes. For the database:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec -T postgres pg_dump -U lms -Fc lms > lms-$(date +%F).dump
```

Restore with `pg_restore --clean --dbname lms`. Redis holds nothing that cannot be rebuilt.

## Upgrading

```bash
git pull
make prod-up      # rebuilds images; the migrate service runs before the app restarts
```

To deploy published images instead of building on the server, replace each `build:` with
`image: ghcr.io/<owner>/lms-backend:<version>` or `lms-web:<version>`; a `v*` tag publishes both.

## Checklist

- [ ] Every value in `.env.production` is set; the secret key and database password are random.
- [ ] TLS terminates in front of `web` and forwards `X-Forwarded-Proto`.
- [ ] SMTP works: sign up with a real address and receive the verification email.
- [ ] `GET /api/health/` is healthy through the public URL.
- [ ] Backups of `pgdata` and `media` run on a schedule, and a restore has been tried.
- [ ] `seed_demo` was not run (it refuses unless `DEBUG` is on).
