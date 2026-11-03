#!/usr/bin/env bash
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
#  run_xela.sh — Standalone launcher for Xela uSkin tactile sensors (DG-5F-R)
# ==============================================================================

set -e

echo "=================================================="
echo "   Initializing Xela uSkin Tactile Sensors...     "
echo "=================================================="

VSCOM_PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n 1 || true)

if [ -z "$VSCOM_PORT" ]; then
    echo "[ERROR] No VSCOM USB-CAN adapter detected on /dev/ttyUSB*!"
    echo "Please verify the USB connection of the CAN adapter."
    exit 1
fi

echo "[INFO] VSCOM adapter detected on: $VSCOM_PORT"
echo "[INFO] Configuring slcan0 CAN interface at 1 Mbps..."
sudo ip link set slcan0 down 2>/dev/null || true
sudo killall slcand 2>/dev/null || true
sudo slcand -o -s8 -t hw -S 3000000 "$VSCOM_PORT" slcan0
sudo ip link set slcan0 up

echo "[SUCCESS] CAN interface slcan0 is UP."

XELA_DIR="${XELA_DIR:-/etc/xela}"
if [ -x "$XELA_DIR/xela_server" ]; then
    echo "[INFO] Launching Xela Server (WebSocket port 5000)..."
    gnome-terminal --title="Xela Server" -- bash -c "cd '$XELA_DIR' && ./xela_server; exec bash" &
    sleep 2
    echo "[INFO] Launching Xela 3D Visualizer..."
    gnome-terminal --title="Xela Visualizer" -- bash -c "cd '$XELA_DIR' && ./xela_viz; exec bash" &
fi
