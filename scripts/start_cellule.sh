#!/usr/bin/env bash
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
#  start_cellule.sh
#  ================
#  Master multi-terminal launcher for the robotic manipulation cell:
#    1. Universal Robots UR5e Arm (ROS 2 Driver + RViz2)
#    2. Tesollo DG-5F Hand + Xela uSkin Tactile Sensors (./run_hand.sh)
#    3. Tesollo 20-DoF Robot State Publisher & Joint State Broadcaster
#    4. [Optional] OnRobot HEX-E v2 6-Axis Force/Torque Sensor Acquisition
#
#  Usage:
#    ./scripts/start_cellule.sh               # Launch UR5e + Tesollo + Xela + TF/JointState
#    ./scripts/start_cellule.sh --with-sensor # Include OnRobot HEX-E v2 live acquisition
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
ROS_SETUP="/opt/ros/humble/setup.bash"
if [ ! -f "$ROS_SETUP" ] && [ -f "/opt/ros/jazzy/setup.bash" ]; then
    ROS_SETUP="/opt/ros/jazzy/setup.bash"
fi
WS_SETUP="$WORKSPACE_DIR/install/setup.bash"

ROBOT_IP="${ROBOT_IP:-192.168.3.101}"
TESOLLO_IP="${TESOLLO_IP:-169.254.186.72}"

C_BLUE='\033[1;34m'
C_CYAN='\033[1;36m'
C_GREEN='\033[1;32m'
C_YELLOW='\033[1;33m'
C_RED='\033[1;31m'
C_RESET='\033[0m'
C_BOLD='\033[1m'

clear
echo -e "${C_CYAN}${C_BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║          UR5e + TESOLLO DG-5F + ONROBOT HEX-E v2 — MASTER LAUNCHER           ║"
echo "╠══════════════════════════════════════════════════════════════════════════════╣"
echo "║  🦾 UR5e IP          : $ROBOT_IP                                        ║"
echo "║  🖐  Tesollo IP       : $TESOLLO_IP:502 (Modbus TCP / DGSDK)             ║"
echo "║  🖐  Hand & Tactile   : run_hand.sh (Xela CAN Server + 3D Viz)                ║"
echo "║  🔗 ROS 2 TF & State : dg5f_rsp.launch.py + tesollo_joint_state_broadcaster  ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${C_RESET}"

LAUNCH_SENSOR=false
if [ "${1:-}" == "--with-sensor" ] || [ "${1:-}" == "-s" ]; then
    LAUNCH_SENSOR=true
    echo -e "${C_YELLOW}⚡ Option enabled: OnRobot HEX-E v2 Force/Torque acquisition included.${C_RESET}"
else
    echo -e "${C_BLUE}ℹ️  Standard mode: Run with --with-sensor to include OnRobot F/T acquisition.${C_RESET}"
fi
echo ""

# ==============================================================================
# [ 1 ] UR5e ROS 2 Driver + RViz2
# ==============================================================================
echo -e "${C_BOLD}[1/3] Launching UR5e ROS 2 Driver + RViz2...${C_RESET}"
gnome-terminal \
    --title="[UR5e] ROS 2 Driver" \
    --geometry=100x25+50+50 \
    -- bash -c "
        source '$ROS_SETUP' 2>/dev/null || true
        source '$WS_SETUP' 2>/dev/null || true
        echo -e '${C_BLUE}${C_BOLD}=== TERMINAL 1: UR5e ROS 2 DRIVER ===${C_RESET}'
        echo -e '${C_YELLOW}▶ On Teach Pendant: Enable Remote Control and press Play ▶ on External Control program.${C_RESET}'
        ros2 launch ur_robot_driver ur5e.launch.py robot_ip:='$ROBOT_IP' launch_rviz:=true
        exec bash
    " &
sleep 2

# ==============================================================================
# [ 2 ] Tesollo DG-5F + Xela Tactile Sensors (run_hand.sh)
# ==============================================================================
echo -e "${C_BOLD}[2/3] Launching Tesollo DG-5F + Xela Tactile Suite...${C_RESET}"
gnome-terminal \
    --title="[TESOLLO + XELA] Hardware Initialization" \
    --geometry=85x20+150+150 \
    -- bash -c "
        cd '$SCRIPT_DIR'
        ./run_hand.sh
        exec bash
    " &
sleep 2

# ==============================================================================
# [ OPTIONAL ] OnRobot HEX-E v2 Force/Torque Sensor Acquisition
# ==============================================================================
if [ "$LAUNCH_SENSOR" = true ]; then
    echo -e "${C_BOLD}[+] Launching OnRobot HEX-E v2 Force/Torque Acquisition...${C_RESET}"
    gnome-terminal \
        --title="[ONROBOT HEX-E v2] 100 Hz EtherCAT F/T" \
        --geometry=95x22+300+300 \
        -- bash -c "
            source '$ROS_SETUP' 2>/dev/null || true
            echo -e '${C_RED}${C_BOLD}=== REAL-TIME ONROBOT HEX-E v2 ETHERCAT ACQUISITION ===${C_RESET}'
            sudo python3 '$SCRIPT_DIR/test_onrobot_ft.py' --format all
            exec bash
        " &
    sleep 1
fi

# ==============================================================================
# [ 3 ] Tesollo 20-DoF ROS 2 TF & Joint State Broadcaster
# ==============================================================================
echo -e "${C_BOLD}[3/3] Launching Tesollo 20-DoF ROS 2 TF & Joint State Broadcaster...${C_RESET}"
gnome-terminal \
    --title="[ROS 2] Tesollo 20-DoF TF & Joint States" \
    --geometry=100x24+350+100 \
    -- bash -c "
        source '$ROS_SETUP' 2>/dev/null || true
        source '$WS_SETUP' 2>/dev/null || true
        ros2 launch '$WORKSPACE_DIR/launch/dg5f_rsp.launch.py' &
        sleep 1
        python3 '$SCRIPT_DIR/tesollo_joint_state_broadcaster.py'
        exec bash
    " &

echo ""
echo -e "${C_GREEN}${C_BOLD}✔ All cell components started! Run ./scripts/stop_cellule.sh to shut down cleanly.${C_RESET}"
