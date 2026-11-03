#!/usr/bin/env bash
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
# install_sdk.sh — Global installer for Tesollo DGSDK v1.6.0 headers & library
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="${SCRIPT_DIR}/DGSDK"
LIB_PATH="${SDK_DIR}/libDGSDK.so"

echo "=== Installing Tesollo DGSDK v1.6.0 globally ==="

if [ ! -f "${SDK_DIR}/DGSDK.h" ] || [ ! -f "${SDK_DIR}/DGDataTypes.h" ]; then
    echo "Error: SDK headers not found in ${SDK_DIR}!"
    exit 1
fi

if [ ! -f "${LIB_PATH}" ]; then
    echo "Error: Shared library libDGSDK.so not found at ${LIB_PATH}!"
    exit 1
fi

echo "Copying headers to /usr/local/include/..."
sudo cp "${SDK_DIR}/DGSDK.h" /usr/local/include/
sudo cp "${SDK_DIR}/DGDataTypes.h" /usr/local/include/

echo "Copying shared library to /usr/local/lib/..."
sudo cp "${LIB_PATH}" /usr/local/lib/

echo "Updating dynamic linker cache (ldconfig)..."
sudo ldconfig

echo "Tesollo DGSDK installed successfully!"
echo "  Headers : /usr/local/include/{DGSDK.h, DGDataTypes.h}"
echo "  Library : /usr/local/lib/libDGSDK.so"
