.PHONY: up down build logs test lint clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest
	cd frontend && npm test

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

clean:
	docker compose down -v
