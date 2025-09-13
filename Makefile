.PHONY: up down logs health seed lint test

up:
	docker compose -f docker-compose.ai.yml up -d --build

down:
	docker compose -f docker-compose.ai.yml down -v

logs:
	docker compose -f docker-compose.ai.yml logs -f --tail=200 ai-core

health:
	curl -s http://localhost:8000/health | jq

seed:
	docker compose -f docker-compose.ai.yml exec vector psql -U postgres -d hacs -c "INSERT INTO items(embedding,text,metadata) VALUES('[0.001$(for i in $$(seq 2 384); do printf ",0.001"; done)]', 'Local context example', '{"source":"seed"}');"

lint:
	@echo "✔️  (опц.) подключи ruff/black/mypy в отдельном tox/pyproject"

test:
	curl -s -X POST http://localhost:8000/act -H "Content-Type: application/json" -d '{"text":"what is resonance?"}' | jq
