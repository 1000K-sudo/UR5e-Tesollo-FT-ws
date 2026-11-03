<!-- 
==============================================================================
Author: Kamil BENMADI
Email: kamil.benmadi@sigma-clermont.fr
GitHub: https://github.com/1000K-sudo
LinkedIn: https://www.linkedin.com/in/kamilb-
==============================================================================
-->

# Tesollo DG-5F SDK (v1.6.0) & Xela uSkin Tactile Sensor Setup Guide

> **Model:** Tesollo Delto Gripper DG-5F-R (Right Hand, 20-DoF)  
> **Hand Communication:** Ethernet (Modbus TCP, IP `169.254.186.72`, Port `502`)  
> **SDK Version:** DGSDK v1.6.0 (`libDGSDK.so`)  
> **Tactile Array:** Xela Robotics uSkin 3-Axis Magnetic Tactile Sensors (CAN `slcan0` @ 1 Mbps)

---

## 1. Prerequisites

- Ubuntu 22.04 LTS (Jammy) or Ubuntu 24.04 LTS (Noble)
- ROS 2 Humble or ROS 2 Jazzy
- `cmake`, `g++`, `build-essential`, `can-utils`, `ethtool`
- Python 3 with `pysoem`, `numpy`, `matplotlib`

Install all system and ROS 2 dependencies automatically:

```bash
sudo ./sdk_tools/install_dependencies.sh
```

---

## 2. Installing the Tesollo C/C++ SDK (`DGSDK` v1.6.0)

The official headers (`DGSDK.h`, `DGDataTypes.h`) and shared library (`libDGSDK.so`) are located in [`sdk_tools/DGSDK/`](../sdk_tools/DGSDK/).

To install them globally into `/usr/local/include` and `/usr/local/lib` and compile the C++ CLI utilities (`tesollo_cmd` and `simple_test`):

```bash
./ur5e_cell.sh build
```

Verify the installation:
```bash
ls -l /usr/local/include/DGSDK.h /usr/local/include/DGDataTypes.h
ls -l /usr/local/lib/libDGSDK.so
ldconfig -p | grep DGSDK
```

---

## 3. Network Configuration for the Tesollo DG-5F Hand

The Tesollo DG-5F uses the factory link-local IPv4 address **`169.254.186.72`** (Modbus TCP port `502`). Assign a static address on the same subnet to your workstation's Ethernet interface (e.g., `enp2s0`):

```bash
sudo ip addr add 169.254.186.10/16 dev enp2s0
sudo ip link set enp2s0 up
```

Verify connectivity and Modbus TCP port availability:
```bash
ping -c 3 169.254.186.72
nc -zv 169.254.186.72 502
```

### Persistent Netplan Configuration (Optional)
Create `/etc/netplan/99-tesollo.yaml`:
```yaml
network:
  version: 2
  ethernets:
    enp2s0:
      addresses:
        - 192.168.3.10/24
        - 169.254.186.10/16
```
Apply with `sudo netplan apply`.

---

## 4. Xela uSkin 3-Axis Tactile Sensor Setup (CAN Bus)

The fingertips and palm of the Tesollo DG-5F-R hand are equipped with **Xela uSkin** high-density 3-axis tactile taxels communicating over a high-speed **CAN bus (1 Mbps)** via a **VSCOM USB-CAN** adapter.

### Hardware Connections
1. Connect the **VSCOM USB-CAN adapter** to a USB port on the PC (detected as `/dev/ttyUSB0`).
2. Connect the **5V USB power cable** for the tactile array (verify the blue power LED is lit).

### Automated Initialization
Run [`scripts/run_xela.sh`](../scripts/run_xela.sh) or [`scripts/run_hand.sh`](../scripts/run_hand.sh) to automatically:
1. Detect `/dev/ttyUSB*`.
2. Initialize the `slcan0` SocketCAN interface at 1 Mbps (`slcand -o -s8 -t hw -S 3000000`).
3. Deploy the sensor mapping file [`sdk_tools/xela_config/xServ.ini`](../sdk_tools/xela_config/xServ.ini) and [`sdk_tools/xela_config/DG-5F-R.xela`](../sdk_tools/xela_config/DG-5F-R.xela).
4. Start the Xela WebSocket server (`localhost:5000`) and 3D visualizer.

For ROS 2 integration, the [`src/xela_server_ros2`](../src/xela_server_ros2), [`src/xela_models`](../src/xela_models), and [`src/xela_description`](../src/xela_description) packages publish tactile taxel forces and 3D frames directly into the ROS 2 ecosystem.

---

## 5. Official Manuals & Reference Documents

All hardware manuals and kinematic datasheets are archived in [`docs/manuals/`](manuals/):
- **[DG-5F_User_Manual_En_v1.1.4.pdf](manuals/DG-5F_User_Manual_En_v1.1.4.pdf):** Complete Tesollo DG-5F hardware, Modbus register, and electrical manual.
- **[Delto_Gripper_Manager_and_SDK_User_Manual_ver_1_6_0_EN.pdf](manuals/Delto_Gripper_Manager_and_SDK_User_Manual_ver_1_6_0_EN.pdf):** Official Delto Gripper Manager GUI and C/C++ `DGSDK v1.6.0` reference manual.
- **[Delto_Gripper_5F_DH_Parameter.pdf](manuals/Delto_Gripper_5F_DH_Parameter.pdf):** Official Denavit-Hartenberg (DH) kinematic parameters for all 5 fingers.
- **[XelaSensorsSetupinTesolloHand.pdf](manuals/XelaSensorsSetupinTesolloHand.pdf):** Integration guide for Xela uSkin tactile pads on the Tesollo DG-5F hand.
- **[XELA_software_manual_1.8.1_237601.pdf](manuals/XELA_software_manual_1.8.1_237601.pdf):** Xela Server, WebSocket API, and ROS 2 driver manual.
- **[VSCAN_Manual.pdf](manuals/VSCAN_Manual.pdf):** VSCOM USB-CAN adapter hardware and `slcand` SocketCAN configuration manual.

---

*Author: Kamil BENMADI (<kamil.benmadi@sigma-clermont.fr>) — [GitHub](https://github.com/1000K-sudo) | [LinkedIn](https://www.linkedin.com/in/kamilb-)*
