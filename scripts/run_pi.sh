#!/usr/bin/env bash
set -e

PROJECT_DIR="$HOME/TruLight"

cd "$PROJECT_DIR/api"
sudo "$HOME/TruLight/api/.venv/bin/python" -m uvicorn main:app --host 0.0.0.0 --port 8000


#Power on web, to be tested in singular script 
cd "$PROJECT_DIR/web/build"
python3 -m http.server 3000

cd $PROJECT_DIR
DISPLAY=:0 chromium-browser --kiosk http://localhost:3000