#!/usr/bin/env bash
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
#  stop_cellule.sh
#  ===============
#  Cleanly stops all ROS 2 nodes, drivers, tactile servers, and CAN/EtherCAT
#  processes for the UR5e + Tesollo DG-5F + OnRobot HEX-E v2 robotic cell.
# ==============================================================================

C_RED='\033[1;31m'
C_GREEN='\033[1;32m'
C_YELLOW='\033[1;33m'
C_RESET='\033[0m'
C_BOLD='\033[1m'

echo -e "${C_YELLOW}${C_BOLD}Stopping all UR5e + Tesollo + OnRobot cell components...${C_RESET}"

# 1. Tesollo state broadcasters & TF publishers
echo "  -> Stopping Tesollo ROS 2 nodes..."
pkill -f "tesollo_joint_state_broadcaster.py" 2>/dev/null || true
pkill -f "dg5f_rsp.launch.py" 2>/dev/null || true
pkill -f "tool0_to_tesollo_tf" 2>/dev/null || true

# 2. RViz2
echo "  -> Closing RViz2..."
pkill -f "rviz2" 2>/dev/null || true

# 3. UR5e ROS 2 Driver
echo "  -> Stopping UR5e ROS 2 driver..."
pkill -f "ur5e.launch.py" 2>/dev/null || true
pkill -f "ur_ros2_control_node" 2>/dev/null || true
pkill -f "dashboard_client" 2>/dev/null || true
pkill -f "robot_state_helper" 2>/dev/null || true
pkill -f "urscript_interface" 2>/dev/null || true

# 4. Tesollo DGManager & Sensors (Xela uSkin, OnRobot HEX-E v2)
echo "  -> Stopping DGManager, Xela tactile server, and OnRobot F/T acquisition..."
pkill -f "DGManager" 2>/dev/null || true
pkill -f "run_hand" 2>/dev/null || true
pkill -f "xela_server" 2>/dev/null || true
pkill -f "xela_viz" 2>/dev/null || true
pkill -f "test_onrobot_ft.py" 2>/dev/null || true

# 5. Release CAN slcan0 interface if active
sudo killall slcand 2>/dev/null || true
sudo ip link set slcan0 down 2>/dev/null || true

sleep 1
echo -e "${C_GREEN}${C_BOLD}✔ All cell processes have been stopped cleanly.${C_RESET}"
