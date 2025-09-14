#!/usr/bin/env bash
set -euo pipefail

echo "==> HACS macOS installer"

# 0) Проверки
command -v python3 >/dev/null || { echo "Install Python3 first"; exit 1; }
command -v pip3 >/dev/null    || { echo "Install pip3 first"; exit 1; }
command -v go >/dev/null      || { echo "Install Go 1.22+ first"; exit 1; }

# 1) Путь до репы (по умолчанию: ~/iamcore)
REPO_DIR="${REPO_DIR:-$HOME/iamcore}"
if [[ ! -d "$REPO_DIR" ]]; then
  echo "Repo dir not found at $REPO_DIR"
  echo "Clone and set REPO_DIR, e.g.: git clone https://github.com/hacsworld/iamcore.git ~/iamcore"
  exit 1
fi

cd "$REPO_DIR"

# 2) Core deps (venv)
echo "==> Setting up Python venv (core)"
cd core
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
deactivate
cd ..

# 3) Build agent binary and install to /usr/local/bin
echo "==> Building agent"
cd agent
go mod tidy
GOFLAGS="-trimpath" go build -o hacs-agent main.go
sudo mkdir -p /usr/local/bin
sudo cp -f hacs-agent /usr/local/bin/hacs-agent
cd ..

# 4) LaunchAgent plist
echo "==> Installing launchd plist"
mkdir -p "$HOME/Library/LaunchAgents"
# подменяем ~ в WorkingDirectory: launchd не разворачивает тильду
PLIST_SRC="launchd/com.hacs.agent.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.hacs.agent.plist"
# Прописываем абсолютный путь до WorkingDirectory
ABS_REPO_DIR=$(python3 - <<PY
import os,sys
print(os.path.abspath(os.environ["REPO_DIR"]) if "REPO_DIR" in os.environ else os.path.abspath("$REPO_DIR"))
PY
)
# Сформируем финальный plist с заменой '~/iamcore' -> '$ABS_REPO_DIR'
/usr/bin/sed "s#~/iamcore#${ABS_REPO_DIR}#g" "$PLIST_SRC" > "$PLIST_DST"

launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
launchctl start com.hacs.agent || true

echo
echo "✅ Done. Agent set to auto-start at login."
echo "  Logs:   ~/Library/Logs/hacs-agent.out.log / hacs-agent.err.log"
echo "  Control: launchctl stop|start com.hacs.agent"
echo
echo "Tip: run once to pair:  /usr/local/bin/hacs-agent"
