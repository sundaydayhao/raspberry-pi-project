#!/bin/bash

set -e

echo "========================================="
echo "  Raspberry Pi Plate Recognition Install"
echo "========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo:"
    echo "  sudo bash install.sh"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
VENV_DIR="$SCRIPT_DIR/venv"
TMP_DIR="$SCRIPT_DIR/.tmp"

detect_optional_pkg() {
    local pkg="$1"
    local policy
    policy="$(apt-cache policy "$pkg" 2>/dev/null || true)"
    if printf '%s\n' "$policy" | grep -q "Candidate:" && \
       ! printf '%s\n' "$policy" | grep -q "Candidate: (none)"; then
        echo "$pkg"
    fi
}

echo "Step 1/4: update apt index..."
apt-get update

echo ""
echo "Step 2/4: install system packages..."
OPTIONAL_PACKAGES=()
for pkg in python3-picamera2 libcamera-apps fonts-noto-cjk; do
    found="$(detect_optional_pkg "$pkg")"
    if [ -n "$found" ]; then
        OPTIONAL_PACKAGES+=("$found")
    fi
done

apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-opencv \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libatlas-base-dev \
    "${OPTIONAL_PACKAGES[@]}"

echo ""
echo "Step 3/4: create virtualenv..."
if [ ! -x "$VENV_DIR/bin/python3" ]; then
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

mkdir -p "$TMP_DIR"
"$VENV_DIR/bin/python3" -m pip install --upgrade pip
"$VENV_DIR/bin/python3" -m pip install -r requirements.txt

if "$VENV_DIR/bin/python3" -m pip show numpy >/dev/null 2>&1; then
    echo "Removing venv-local NumPy to keep OpenCV compatible with system NumPy..."
    TMPDIR="$TMP_DIR" "$VENV_DIR/bin/python3" -m pip uninstall -y numpy || true
fi

echo ""
echo "Step 4/4: finalize..."
chmod +x "$SCRIPT_DIR/main.py"

echo ""
echo "Install complete."
echo ""
echo "Run with image:"
echo "  $VENV_DIR/bin/python3 main.py --image /path/to/car.jpg --show"
echo ""
echo "Run with camera:"
echo "  $VENV_DIR/bin/python3 main.py --camera --camera-engine auto --show"
echo ""
echo "If camera access fails, add your user to the video group and reboot:"
echo "  sudo usermod -aG video \$SUDO_USER"
