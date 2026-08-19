PYTHON ?= venv/Scripts/python.exe

.PHONY: help up down build etl etl-docker test lint clean logs

help:
	@echo "Available commands:"
	@echo "  make up      - Start all services"
	@echo "  make down    - Stop all services"
	@echo "  make build   - Build Docker images"
	@echo "  make etl     - Run ETL pipeline locally"
	@echo "  make etl-docker - Run ETL pipeline inside Docker"
	@echo "  make test    - Run pytest"
	@echo "  make lint    - Run flake8"
	@echo "  make clean   - Remove containers and volumes"
	@echo "  make logs    - Follow service logs"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

etl:
	$(PYTHON) -m app.etl.run_pipeline

etl-docker:
	docker compose run --rm --build fastapi python -m app.etl.run_pipeline

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

lint:
	flake8 app/ tests/ --max-line-length=100

clean:
	docker compose down -v --remove-orphans

logs:
	docker compose logs -f
