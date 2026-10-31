.PHONY: dev-backend dev-frontend dev test test-unit test-integration test-security verify migrate makemigrations lint clean build-frontend

PYTHON := ./backend/venv/bin/python
ALEMBIC := ./backend/venv/bin/alembic
PYTEST := ./backend/venv/bin/pytest
UVICORN := ./backend/venv/bin/uvicorn
PNPM := pnpm

dev-backend:
	cd backend && ../$(UVICORN) app.main:app --host 127.0.0.1 --port 8000 --reload

dev-worker:
	cd backend && ../$(PYTHON) -m celery -A app.workers.celery_app.celery worker --loglevel=info

dev-beat:
	cd backend && ../$(PYTHON) -m celery -A app.workers.celery_app.celery beat --loglevel=info

dev-frontend:
	cd frontend && $(PNPM) dev

test:
	cd backend && ../$(PYTEST) tests/ -v

verify:
	$(PYTHON) scripts/verify_system.py

test-unit:
	cd backend && ../$(PYTEST) tests/unit/ -v

test-integration:
	cd backend && ../$(PYTEST) tests/integration/ -v

test-security:
	cd backend && ../$(PYTEST) tests/security/ -v

migrate:
	cd backend && ../$(ALEMBIC) upgrade head

makemigrations:
	cd backend && ../$(ALEMBIC) revision --autogenerate -m "$(m)"

build-frontend:
	cd frontend && $(PNPM) build
