run:
	uvicorn core.app:app --host 127.0.0.1 --port 8000 --reload

sanity:
	bash scripts/sanity.sh

test:
	pytest -v
