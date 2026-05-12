#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_PORT="/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0"
DEFAULT_PACKAGE="$REPO_ROOT/build/amigo-diag-official-shell-kboot.kfpkg"

PORT="${AMIGO_PORT:-$DEFAULT_PORT}"
PACKAGE="${1:-$DEFAULT_PACKAGE}"
BAUD="${AMIGO_BAUD:-115200}"
WAIT_SECONDS="${AMIGO_WAIT_SECONDS:-0}"

usage() {
    cat <<EOF
Usage: firmware/scripts/flash-amigo-diag.sh [package]

Safely flash the Amigo LCD/backlight diagnostic package.

Environment:
  AMIGO_PORT          Serial port, default: $DEFAULT_PORT
  AMIGO_BAUD          Flash baudrate, default: 115200
  AMIGO_WAIT_SECONDS  Wait for serial port before failing, default: 0
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if [ ! -f "$PACKAGE" ]; then
    echo "Missing package: $PACKAGE" >&2
    exit 1
fi

deadline=$((SECONDS + WAIT_SECONDS))
while [ ! -e "$PORT" ]; do
    if [ "$WAIT_SECONDS" -le 0 ] || [ "$SECONDS" -ge "$deadline" ]; then
        echo "Amigo serial port not found: $PORT" >&2
        echo "Refusing to flash any non-Sipeed fallback port." >&2
        exit 2
    fi
    sleep 1
done

echo "Using port: $PORT"
echo "Using package: $PACKAGE"
sha256sum "$PACKAGE"

sudo nice -n 10 python3 "$REPO_ROOT/firmware/Kboot/build/ktool.py" \
    -B goE \
    -b "$BAUD" \
    -p "$PORT" \
    "$PACKAGE"
