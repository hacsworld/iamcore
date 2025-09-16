.PHONY: run sanity
run:
	uvicorn core.app:app --host 127.0.0.1 --port 8000 --reload
sanity:
	API=http://127.0.0.1:8000 API_KEY=$$(grep ^API_KEY .env | cut -d= -f2) ./scripts/sanity.sh
