# Makefile for TerraSim

.PHONY: help install install-dev lint format test coverage clean build docs serve docker-build

help:
	@echo "TerraSim Development Commands"
	@echo "==============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run all linters (pylint, mypy, bandit)"
	@echo "  make format           Format code with black and isort"
	@echo "  make check            Run all checks without modifying"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run tests with coverage"
	@echo "  make coverage         Generate detailed coverage report"
	@echo "  make test-watch       Run tests in watch mode"
	@echo ""
	@echo "Development:"
	@echo "  make run              Start API server"
	@echo "  make run-desktop      Start desktop application"
	@echo "  make db-migrate       Run database migrations"
	@echo ""
	@echo "Building:"
	@echo "  make build            Build distribution packages"
	@echo "  make clean            Clean build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run Docker container"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             Build documentation"
	@echo "  make docs-serve       Serve docs locally"
	@echo ""

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

format:
	black backend/ frontend/ tests/
	isort backend/ frontend/ tests/

lint:
	pylint backend/ || true
	mypy backend/ || true
	bandit -r backend/ || true
	black --check backend/ frontend/ tests/ || true
	isort --check-only backend/ frontend/ tests/ || true

check: lint
	@echo "All checks passed!"

test:
	pytest --cov=backend --cov-report=html tests/
	@echo "Coverage report generated in htmlcov/index.html"

coverage: test
	coverage report
	coverage html
	@echo "Open htmlcov/index.html to view coverage"

test-watch:
	pytest-watch

run:
	python app.py

run-desktop:
	python terrasim.py

db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

db-create-migration:
	alembic revision --autogenerate -m "$(msg)"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build: clean
	python -m build

docs:
	mkdocs build

docs-serve:
	mkdocs serve

docker-build:
	docker build -t terrasim:latest .

docker-run:
	docker-compose up

docker-dev:
	docker-compose -f docker-compose.dev.yml up

.DEFAULT_GOAL := help
