#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/pi//TruLight"  # adjust to your repo path on the Pi

sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev build-essential

cd "$PROJECT_DIR/api"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-pi.txt

