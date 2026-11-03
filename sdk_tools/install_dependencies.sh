#!/usr/bin/env bash
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
# install_dependencies.sh
# Tesollo Hand DG-5F — Auto-detect Ubuntu/ROS 2 version and install packages
#
# Supported distributions:
#   - Ubuntu 22.04 (Jammy)  -> ROS 2 Humble / Iron
#   - Ubuntu 24.04 (Noble)  -> ROS 2 Jazzy / Rolling
#
# Usage:
#   chmod +x install_dependencies.sh
#   sudo ./install_dependencies.sh
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }

if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run with sudo or as root."
    echo "  Usage:  sudo ./install_dependencies.sh"
    exit 1
fi

if [[ ! -f /etc/os-release ]]; then
    log_error "Cannot detect OS. /etc/os-release not found."
    exit 1
fi

source /etc/os-release

log_info "Detected OS: ${PRETTY_NAME}"
log_info "Version ID:  ${VERSION_ID}"
log_info "Codename:    ${VERSION_CODENAME}"

ROS2_DISTRO="none"
for distro in humble iron jazzy rolling; do
    if [[ -d "/opt/ros/${distro}" ]]; then
        ROS2_DISTRO="${distro}"
        break
    fi
done

if [[ "${ROS2_DISTRO}" != "none" ]]; then
    log_info "Detected ROS 2 distribution: ${ROS2_DISTRO}"
else
    log_warn "No ROS 2 installation detected under /opt/ros/."
    log_warn "Only system dependencies will be installed."
fi

case "${VERSION_ID}" in
    "22.04")
        ALSA_PKG="libasound2"
        LIBGTK_PKG="libgtk-3-0"
        LIBGDK_PKG="libgdk-pixbuf-2.0-0"
        ;;
    "24.04")
        ALSA_PKG="libasound2t64"
        LIBGTK_PKG="libgtk-3-0t64"
        LIBGDK_PKG="libgdk-pixbuf-2.0-0"
        ;;
    *)
        ALSA_PKG="libasound2"
        LIBGTK_PKG="libgtk-3-0"
        LIBGDK_PKG="libgdk-pixbuf-2.0-0"
        ;;
esac

if ! apt-cache show "${ALSA_PKG}" &>/dev/null; then
    ALSA_PKG="libasound2"
fi
if ! apt-cache show "${LIBGTK_PKG}" &>/dev/null; then
    LIBGTK_PKG="libgtk-3-0"
fi

BUILD_PKGS=(
    build-essential
    cmake
    g++
    pkg-config
    can-utils
    ethtool
)

GUI_PKGS=(
    libnss3
    libnspr4
    libatk1.0-0
    libatk-bridge2.0-0
    libcups2
    libxkbcommon0
    libepoxy0
    "${LIBGTK_PKG}"
    "${LIBGDK_PKG}"
    libpango-1.0-0
    libpangocairo-1.0-0
    libxcb1
    libx11-6
    "${ALSA_PKG}"
    libxrandr2
    libxcomposite1
    libxdamage1
    libxext6
    libxfixes3
    libdrm2
    libgbm1
    libxshmfence1
)

NETWORK_PKGS=(
    net-tools
    iproute2
    netcat-openbsd
)

ROS2_PKGS=()
if [[ "${ROS2_DISTRO}" != "none" ]]; then
    ROS2_PKGS=(
        "ros-${ROS2_DISTRO}-ros-base"
    )
fi

log_info "Refreshing apt package cache..."
apt-get update -qq

log_info "Installing build & CAN/EtherCAT tools..."
apt-get install -y "${BUILD_PKGS[@]}"
log_success "Build tools installed."

log_info "Installing GUI libraries..."
apt-get install -y "${GUI_PKGS[@]}"
log_success "GUI libraries installed."

log_info "Installing network diagnostic tools..."
apt-get install -y "${NETWORK_PKGS[@]}"
log_success "Network tools installed."

if [[ ${#ROS2_PKGS[@]} -gt 0 ]]; then
    log_info "Installing ROS 2 (${ROS2_DISTRO}) packages..."
    apt-get install -y "${ROS2_PKGS[@]}"
    log_success "ROS 2 packages installed."
fi

echo ""
echo "=============================================="
echo -e "${GREEN}  All dependencies installed successfully!${NC}"
echo "=============================================="
