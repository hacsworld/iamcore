#!/usr/bin/env bash
set -e

echo "==> Installing HACS Local Core deps..."
cd core
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "==> Running core on 127.0.0.1:8000"
nohup python app.py >/tmp/hacs-core.log 2>&1 &
deactivate
cd ..

echo "==> Building agent..."
cd agent
if ! command -v go >/dev/null 2>&1; then
  echo "Go is required. Install Go 1.22+ and re-run."
  exit 1
fi
go mod tidy
go build -o hacs-agent main.go
echo "==> Agent built at agent/hacs-agent"
cd ..

echo "==> Done. Start agent with: ./agent/hacs-agent"
