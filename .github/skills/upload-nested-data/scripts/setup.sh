#!/bin/bash
set -e

# Always resolve paths relative to this script's location
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SKILL_DIR/.venv"
REQUIREMENTS="$SKILL_DIR/requirements.txt"
SENTINEL="$SKILL_DIR/.installed"

# Create venv if it doesn't exist
if [ ! -f "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi

# Install dependencies only if requirements.txt has changed
if [ ! -f "$SENTINEL" ] || [ "$REQUIREMENTS" -nt "$SENTINEL" ]; then
    "$VENV/bin/pip" install --upgrade pip -q
    "$VENV/bin/pip" install -r "$REQUIREMENTS" -q
    touch "$SENTINEL"
    echo '{"status": "success", "message": "Dependencies installed"}'
else
    echo '{"status": "skipped", "message": "Dependencies up to date, nothing to do"}'
fi