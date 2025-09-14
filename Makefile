.PHONY: help setup run build-agent clean docker-up docker-down test

help:
	@echo "Targets:"
	@echo "  setup        - create venv & install core deps"
	@echo "  run          - run local core (uvicorn)"
	@echo "  build-agent  - build Go agent binary"
	@echo "  docker-up    - docker compose up -d"
	@echo "  docker-down  - docker compose down"
	@echo "  test         - quick health tests"

setup:
	cd core && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt

run:
	cd core && . venv/bin/activate && python app.py

build-agent:
	cd agent && go mod tidy && go build -o hacs-agent main.go

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

test:
	curl -fsS http://127.0.0.1:8000/health | jq .
