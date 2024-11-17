.PHONY: install lint test run docker-build docker-run clean dev

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
DOCKER := docker
DOCKER_COMPOSE := docker compose

# Installation
install:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

# Linting
lint:
	flake8 .
	mypy .
	black --check .
	isort --check-only .

# Format code
format:
	black .
	isort .

# Run tests
test:
	pytest tests/

# Run the application
run:
	$(PYTHON) main.py

# Development setup and run
dev: format
	$(DOCKER_COMPOSE) up -d mongodb
	$(PYTHON) main.py

# Docker commands
docker-build:
	$(DOCKER) build -t ai-recruiter .

docker-run:
	$(DOCKER_COMPOSE) up -d

docker-stop:
	$(DOCKER_COMPOSE) down

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 