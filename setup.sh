#!/usr/bin/env bash
# Create the virtualenv and install dependencies. Run once: ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo 'Ready. Render with:  ./generate.py --header "HEADER" --subtitle "subtitle" --footer "footer"'
