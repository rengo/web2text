.PHONY: up down logs migrate seed build prod-up prod-down prod-logs

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

clean-db:
	docker compose exec db psql -U postgres -d web2text -c "TRUNCATE pages, page_contents, scrape_runs CASCADE;"

# Production
prod-up:
	docker compose -f docker-compose.prod.yml up --build -d

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

prod-clean-db:
	docker compose -f docker-compose.prod.yml exec db psql -U postgres -d web2text -c "TRUNCATE pages, page_contents, scrape_runs CASCADE;"
