#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 bootstrap.py \
  --freq 106.2 \
  --sample-rate 2400000 \
  --gain auto \
  --fft-size 1024 \
  --frame-rate 20 \
  --width 1366 \
  --height 768
