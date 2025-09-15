.PHONY: up-blue up-green logs-blue logs-green sanity-blue sanity-green clean stopup-blue:
    docker compose up -d --build hacs-core-blueup-green:
    docker compose up -d --build hacs-core-greenlogs-blue:
    docker logs -f hacs-core-bluelogs-green:
    docker logs -f hacs-core-greensanity-blue:
    API=http://127.0.0.1:8000 API_KEY=${API_KEY} ./scripts/sanity.shsanity-green:
    API=http://127.0.0.1:8001 API_KEY=${API_KEY} ./scripts/sanity.shclean:
    docker compose down -v --remove-orphans  # Grok: remove volumes/orphansstop:
    docker compose stop

