.PHONY: dev migrate shell test lint fmt

dev:            ## run everything with hot reload
	docker compose up --build

migrate:
	docker compose exec backend python manage.py migrate

shell:
	docker compose exec backend python manage.py shell

test:
	cd backend && pytest

lint:
	cd backend && ruff check . && ruff format --check .

fmt:
	cd backend && ruff format . && ruff check --fix .
