#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 main.py \
  --json-path /run/dump1090-fa/aircraft.json \
  --refresh-hz 2 \
  --width 800 \
  --height 480 \
  --gain auto \
  --device-index 0 \
  --rows 12