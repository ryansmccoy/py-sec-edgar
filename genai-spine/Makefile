.PHONY: help install dev run test lint docker-build docker-up docker-down

help:
	@echo "GenAI Spine - Available commands:"
	@echo ""
	@echo "  install      Install dependencies"
	@echo "  dev          Install dev dependencies"
	@echo "  run          Run the API server locally"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  docker-build Build Docker images"
	@echo "  docker-up    Start Docker stack"
	@echo "  docker-down  Stop Docker stack"
	@echo "  pull-models  Pull default Ollama models"

install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev]"

run:
	uvicorn genai_spine.main:app --reload --port 8100

test:
	pytest tests/ -v

lint:
	ruff check src/
	mypy src/

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

pull-models:
	docker compose exec ollama ollama pull llama3.2:latest
	docker compose exec ollama ollama pull nomic-embed-text:latest

# Development shortcuts
dev-up: docker-up pull-models
	@echo "GenAI Spine is ready at http://localhost:8100"
	@echo "Ollama is ready at http://localhost:11434"

dev-down: docker-down

# Quick test
test-health:
	curl -s http://localhost:8100/health | python -m json.tool

test-chat:
	curl -s -X POST http://localhost:8100/v1/chat/completions \
		-H "Content-Type: application/json" \
		-d '{"model": "llama3.2:latest", "messages": [{"role": "user", "content": "Say hello in one sentence."}]}' \
		| python -m json.tool
