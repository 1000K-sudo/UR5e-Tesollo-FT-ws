#!/usr/bin/env bash
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
# ur5e_cell.sh — Unified convenience script for UR5e + Tesollo DG-5F + OnRobot HEX-E v2
#
# Usage:
#   ./ur5e_cell.sh <command> [options]
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROBOT_IP="${ROBOT_IP:-192.168.3.101}"
TESOLLO_IP="${TESOLLO_IP:-169.254.186.72}"
ETHERCAT_IFACE="${ETHERCAT_IFACE:-enxe4fac4b94578}"

# Terminal colors
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
NC=$'\033[0m'

info()    { echo -e "${BLUE}[ur5e_cell]${NC} $*"; }
success() { echo -e "${GREEN}[ur5e_cell]${NC} $*"; }
warn()    { echo -e "${YELLOW}[ur5e_cell]${NC} $*"; }
error()   { echo -e "${RED}[ur5e_cell]${NC} $*" >&2; exit 1; }

source_ros2() {
    set +u
    for distro in jazzy humble iron rolling; do
        if [ -f "/opt/ros/${distro}/setup.bash" ]; then
            source "/opt/ros/${distro}/setup.bash"
            break
        fi
    done
    if [ -f "${SCRIPT_DIR}/install/setup.bash" ]; then
        source "${SCRIPT_DIR}/install/setup.bash"
    fi
    set -u
}

cmd_build() {
    info "Installing Tesollo DGSDK headers & shared library..."
    "${SCRIPT_DIR}/sdk_tools/install_sdk.sh" || warn "Global SDK install skipped (run with sudo if needed)."

    info "Compiling C++ SDK CLI tools (tesollo_cmd, simple_test)..."
    mkdir -p "${SCRIPT_DIR}/sdk_tools/build"
    cmake -S "${SCRIPT_DIR}/sdk_tools" -B "${SCRIPT_DIR}/sdk_tools/build"
    cmake --build "${SCRIPT_DIR}/sdk_tools/build" -j"$(nproc)"
    success "C++ SDK tools compiled in sdk_tools/build/."

    if command -v colcon >/dev/null 2>&1; then
        info "Compiling ROS 2 packages in src/ via colcon..."
        source_ros2
        (cd "${SCRIPT_DIR}" && colcon build --symlink-install)
        success "ROS 2 workspace compiled successfully!"
    else
        warn "colcon not found in current PATH; skipped ROS 2 package build."
    fi
}

cmd_start() {
    exec "${SCRIPT_DIR}/scripts/start_cellule.sh" "$@"
}

cmd_stop() {
    exec "${SCRIPT_DIR}/scripts/stop_cellule.sh"
}

cmd_ur5e() {
    source_ros2
    info "Launching Universal Robots UR5e ROS 2 driver (IP: ${ROBOT_IP})..."
    ros2 launch ur_robot_driver ur5e.launch.py robot_ip:="${ROBOT_IP}" launch_rviz:=true "$@"
}

cmd_hand_rsp() {
    source_ros2
    info "Launching Tesollo DG-5F Robot State Publisher & static TF (tool0 -> right_base_link)..."
    ros2 launch "${SCRIPT_DIR}/launch/dg5f_rsp.launch.py"
}

cmd_hand_broadcaster() {
    source_ros2
    info "Starting real-time 20-DoF joint state broadcaster from hardware encoders..."
    python3 "${SCRIPT_DIR}/scripts/tesollo_joint_state_broadcaster.py"
}

cmd_poses() {
    source_ros2
    if [ $# -eq 0 ]; then
        python3 "${SCRIPT_DIR}/scripts/send_hand_pose_ros2.py" --list
    else
        python3 "${SCRIPT_DIR}/scripts/send_hand_pose_ros2.py" "$@"
    fi
}

cmd_combined_test() {
    source_ros2
    info "Starting synchronized UR5e wrist + Tesollo 5-finger motion test..."
    python3 "${SCRIPT_DIR}/scripts/test_combined_motion.py"
}

cmd_ft_acquire() {
    info "Starting 100 Hz EtherCAT live acquisition on OnRobot HEX-E v2 (${ETHERCAT_IFACE})..."
    sudo python3 "${SCRIPT_DIR}/scripts/test_onrobot_ft.py" --iface "${ETHERCAT_IFACE}" "$@"
}

cmd_ft_plot() {
    if [ $# -eq 0 ]; then
        python3 "${SCRIPT_DIR}/scripts/plot_onrobot_ft.py" "${SCRIPT_DIR}/data/onrobot_ft_recordings" --latest
    else
        python3 "${SCRIPT_DIR}/scripts/plot_onrobot_ft.py" "$@"
    fi
}

cmd_test() {
    info "Running automated unit and integration test suite..."
    python3 -m unittest discover -s "${SCRIPT_DIR}/scripts" -p "test_norms_and_plots.py" -v
    success "All unit and integration tests passed!"
}

cmd_status() {
    echo -e "${CYAN}${BOLD}=== UR5e + Tesollo DG-5F + OnRobot HEX-E v2 Cell Status ===${NC}"
    echo -e "  Workspace Root     : ${SCRIPT_DIR}"
    echo -e "  UR5e Target IP     : ${ROBOT_IP}"
    echo -e "  Tesollo DG-5F IP   : ${TESOLLO_IP}:502"
    echo -e "  EtherCAT Interface : ${ETHERCAT_IFACE}"
    echo -e "  DGSDK Library      : $([ -f /usr/local/lib/libDGSDK.so ] && echo 'Installed (/usr/local/lib/libDGSDK.so)' || echo 'Local (sdk_tools/DGSDK/libDGSDK.so)')"
    echo -e "  Recorded Datasets  : $(ls -1 "${SCRIPT_DIR}/data/onrobot_ft_recordings/"*.csv 2>/dev/null | wc -l) CSV sessions"
    echo -e "  Generated Figures  : $(ls -1 "${SCRIPT_DIR}/docs/figures/"*.png 2>/dev/null | wc -l) PNG figures"
}

cmd_help() {
    cat <<EOF
${CYAN}${BOLD}UR5e + Tesollo DG-5F + OnRobot HEX-E v2 — Management Script${NC}

${BOLD}Usage:${NC}
  ./ur5e_cell.sh <command> [options]

${BOLD}Build & Setup:${NC}
  build                        Install DGSDK, compile C++ tools (tesollo_cmd) & colcon build ROS 2 packages
  status                       Show workspace, network endpoints, SDK & dataset status
  test                         Run unit & integration tests (F/T norms, PDO parser, CSV/NPY exporter)

${BOLD}Cell Orchestration:${NC}
  start [--with-sensor]        Launch complete robotic cell (UR5e + RViz2 + Tesollo/Xela + optional OnRobot F/T)
  stop                         Cleanly stop all cell nodes, drivers, and CAN/EtherCAT interfaces
  ur5e                         Launch UR5e ROS 2 driver and RViz2 standalone
  hand_rsp                     Launch Tesollo DG-5F Robot State Publisher & tool0->hand TF
  hand_broadcaster             Stream real-time 20-DoF joint states from hardware encoders to /joint_states

${BOLD}Dexterous Manipulation & Force/Torque Sensing:${NC}
  poses [pose_name] [--list]   List or apply a certified collision-free 20-DoF posture on Tesollo DG-5F
  combined_test                Execute safe coordinated UR5e + Tesollo 5-finger motion test
  ft_acquire [args]            Run 100 Hz EtherCAT acquisition & software tare for OnRobot HEX-E v2
  ft_plot [file|--latest]      Plot triaxial Forces/Torques and Euclidean norms (||F||, ||T||)
EOF
}

COMMAND="${1:-help}"
shift || true

case "${COMMAND}" in
    build)            cmd_build "$@" ;;
    start)            cmd_start "$@" ;;
    stop)             cmd_stop "$@" ;;
    ur5e)             cmd_ur5e "$@" ;;
    hand_rsp)         cmd_hand_rsp "$@" ;;
    hand_broadcaster) cmd_hand_broadcaster "$@" ;;
    poses)            cmd_poses "$@" ;;
    combined_test)    cmd_combined_test "$@" ;;
    ft_acquire)       cmd_ft_acquire "$@" ;;
    ft_plot)          cmd_ft_plot "$@" ;;
    test)             cmd_test "$@" ;;
    status)           cmd_status "$@" ;;
    help|-h|--help)   cmd_help ;;
    *)                error "Unknown command: ${COMMAND}. Run './ur5e_cell.sh help' for usage." ;;
esac
