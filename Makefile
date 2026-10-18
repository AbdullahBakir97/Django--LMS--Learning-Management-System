.PHONY: help dev migrate seed shell test e2e lint fmt schema images prod-up prod-down

help:           ## list the targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

dev:            ## run everything with hot reload (http://localhost:5173)
	docker compose up --build

migrate:        ## apply database migrations
	docker compose exec backend python manage.py migrate

seed:           ## fill the dev database with demo people, courses, groups and jobs
	docker compose exec backend python manage.py seed_demo

shell:          ## Django shell in the backend container
	docker compose exec backend python manage.py shell

test:           ## backend and frontend unit tests
	cd backend && pytest
	cd frontend && pnpm test:unit --run

e2e:            ## browser smoke test
	cd frontend && pnpm test:e2e

lint:           ## every linter and type check CI runs
	cd backend && ruff check . && ruff format --check .
	cd frontend && pnpm lint && pnpm format:check && pnpm type-check

fmt:            ## format everything
	cd backend && ruff format . && ruff check --fix .
	cd frontend && pnpm format

schema:         ## write the OpenAPI schema to backend/schema.yml
	cd backend && python manage.py spectacular --fail-on-warn --file schema.yml

images:         ## build the production images
	docker build -t lms-backend backend
	docker build -t lms-web frontend

prod-up:        ## run the production stack (needs .env.production)
	docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

prod-down:      ## stop the production stack
	docker compose -f docker-compose.prod.yml --env-file .env.production down
