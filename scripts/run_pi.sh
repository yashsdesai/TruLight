#!/usr/bin/env bash
set -e

PROJECT_DIR="$HOME/TruLight"

cd "$PROJECT_DIR/api"
sudo "$HOME/TruLight/api/.venv/bin/python" -m uvicorn main:app --host 0.0.0.0 --port 8000

