#!/usr/bin/env bash
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
#  run_hand.sh — Unified Launcher: Tesollo DG-5F Hand + Xela uSkin Sensors
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
XELA_CONFIG_SRC="$WORKSPACE_DIR/sdk_tools/xela_config/xServ.ini"
XELA_CONFIG_DST="/etc/xela/xServ.ini"
XELA_DIR="${XELA_DIR:-/etc/xela}"
DGMANAGER_DIR="${DGMANAGER_DIR:-/opt/DGManager}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

clear
echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       Tesollo DG-5F  —  Unified Launch System       ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║    🤖 Hand Controller (Modbus TCP 169.254.186.72)    ║"
echo "║    🖐  Tactile Sensors (Xela uSkin DG-5F-R CAN)      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =============================================================================
# STEP 1: Detect and initialize VSCOM USB-CAN interface (slcan0)
# =============================================================================
echo -e "${BOLD}[ 1/3 ]${NC} Searching for VSCOM USB-CAN adapter..."

VSCOM_PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n 1 || true)
if [ -z "$VSCOM_PORT" ]; then
    echo -e "${RED}[ERROR] No VSCOM adapter detected on /dev/ttyUSB*!${NC}"
    echo "  -> Verify that BOTH USB cables are connected:"
    echo "     • USB-CAN (CAN data) -> PC USB port"
    echo "     • USB Power cable    -> 5V power (blue LED = OK)"
    exit 1
fi
echo -e "  ${GREEN}✔ Adapter found at: $VSCOM_PORT${NC}"

echo -e "${BOLD}[ 2/3 ]${NC} Configuring CAN bus slcan0 at 1 Mbps (sudo required)..."
sudo ip link set slcan0 down 2>/dev/null || true
sudo killall slcand 2>/dev/null || true
sleep 0.3
sudo slcand -o -s8 -t hw -S 3000000 "$VSCOM_PORT" slcan0
sudo ip link set slcan0 up
echo -e "  ${GREEN}✔ CAN interface slcan0 is UP.${NC}"

# =============================================================================
# STEP 2: Install Xela uSkin configuration in /etc/xela/
# =============================================================================
echo -e "${BOLD}[ 3/3 ]${NC} Updating Xela configuration in /etc/xela/..."
sudo mkdir -p /etc/xela/LOG
sudo chmod -R 777 /etc/xela
cp "$XELA_CONFIG_SRC" "$XELA_CONFIG_DST"
echo -e "  ${GREEN}✔ xServ.ini installed in /etc/xela/.${NC}"

if command -v xela_server >/dev/null 2>&1 || [ -x "$XELA_DIR/xela_server" ]; then
    gnome-terminal --title="[XELA] Sensor Server" -- bash -c "cd '$XELA_DIR' && ./xela_server; exec bash" &
    sleep 2
    gnome-terminal --title="[XELA] 3D Visualizer" -- bash -c "cd '$XELA_DIR' && ./xela_viz; exec bash" &
fi

if [ -x "$DGMANAGER_DIR/DGManager" ]; then
    gnome-terminal --title="[TESOLLO] DGManager" -- bash -c "cd '$DGMANAGER_DIR' && ./DGManager; exec bash" &
fi

echo -e "${GREEN}${BOLD}✔ Hand & tactile interfaces initialized (IP: 169.254.186.72, Port: 502).${NC}"
