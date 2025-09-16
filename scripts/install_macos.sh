#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
pip install -r core/requirements.txt
uvicorn core.app:app --host 127.0.0.1 --port 8000 --reload
