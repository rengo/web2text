.PHONY: up down logs migrate seed build

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

migrate:
	docker compose run --rm -w /app/backend backend alembic revision --autogenerate -m "Initial migration"
	docker compose run --rm -w /app/backend backend alembic upgrade head

upgrade:
	docker compose run --rm -w /app/backend backend alembic upgrade head

seed:
	docker compose run --rm backend python -m backend.app.seed

shell-backend:
	docker compose run --rm backend bash
