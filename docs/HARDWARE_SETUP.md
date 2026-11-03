<!-- 
==============================================================================
Author: Kamil BENMADI
Email: kamil.benmadi@sigma-clermont.fr
GitHub: https://github.com/1000K-sudo
LinkedIn: https://www.linkedin.com/in/kamilb-
==============================================================================
-->

# Hardware & Network Architecture Guide: UR5e Arm, OnRobot HEX-E v2 Sensor & Tesollo DG-5F Hand

This document details the hardware architecture, the mechanical assembly stack on the ISO-50 robot tool flange, electrical power requirements, and the dual-NIC network topology required to operate the dexterous manipulation cell.

---

## 1. Dedicated EtherCAT Connection for the OnRobot HEX-E v2 Sensor

The **OnRobot HEX-E v2** 6-axis force/torque sensor **must be connected directly to the control PC via a dedicated Ethernet interface**, physically separated from the IP router used by the UR5e arm and the Tesollo hand.

### Why a Dual-NIC Architecture is Required:
1. **Incompatible with Standard L3 Routers:** The sensor uses the **EtherCAT (CoE — CANopen over EtherCAT)** protocol. It transmits raw Layer-2 Ethernet frames (`EtherType 0x88A4`) without IP addresses or TCP/UDP headers. Consumer routers and standard switches drop or block these raw frames, and concurrent IP traffic (UR5e RTDE at 500 Hz, Modbus TCP, ROS 2 DDS) disrupts EtherCAT real-time determinism.
2. **Incompatible with the UR5e Wrist Tool Connector:** The M8 tool connector on the UR5e wrist only carries 24V digital I/O and an RS-485 serial bus. It does not route raw Ethernet frames and the UR5e control box does not act as an EtherCAT master for external third-party slaves.
3. **Second Ethernet Interface on the Control PC:**
   - **Port 1 (`enp2s0`):** Connected to the ASUS Gigabit router handling IP traffic for the **UR5e arm** (`192.168.3.101`) and **Tesollo DG-5F hand** (`169.254.186.72`).
   - **Port 2 (`enxe4fac4b94578`):** Dedicated **USB 3.0 to Gigabit Ethernet adapter** (TP-Link UE300 / Realtek RTL8153) or PCIe NIC wired directly to the OnRobot HEX-E v2 junction box.

---

## 2. Global Hardware & Network Topology

```text
               ┌─────────────────────────────────────────────────────────────┐
               │                     CONTROL WORKSTATION PC                  │
               │                                                             │
               │   [Ethernet Port 1: enp2s0]         [Ethernet Port 2]       │
               │   IP Network (UR5e + Tesollo)     (Dedicated Raw EtherCAT)  │
               └──────────────┬───────────────────────────────┬──────────────┘
                              │ RJ45 Cable                    │ Direct RJ45 Cable
                              ▼                               ▼
                     ┌─────────────────┐             ┌─────────────────────────┐
                     │   ASUS Router   │             │ OnRobot 24V DC          │
                     └───┬─────────┬───┘             │ Power & Junction Box    │
            RJ45 Cable   │         │ RJ45 Cable      └────────────┬────────────┘
                         ▼         ▼                              │ Sensor Cable
                 ┌──────────┐   ┌──────────────┐                  ▼
                 │   UR5e   │   │ Tesollo Hand │     ┌─────────────────────────┐
                 │  Control │   │   DG-5F-R    │     │  6-Axis F/T Sensor      │
                 │   Box    │   │  (20-DoF)    │     │  OnRobot HEX-E v2       │
                 └──────────┘   └──────────────┘     └─────────────────────────┘
```

---

## 3. Mechanical Stack on the Tool Flange (ISO 9409-1-50-4-M6)

To accurately measure external contact forces and manipulation loads without mechanical short-circuiting, the physical assembly on the UR5e wrist must follow this exact sequence:

```text
       [ UR5e Tool Flange (ISO 50 / 4×M6 bolts, tool0) ]
                             │
                             ▼
       [ OnRobot HEX-E v2 6-Axis Force/Torque Sensor ]
                             │  (Measures ALL downstream forces & torques)
                             ▼
       [ Guidance Handle / Mechanical Adapter Plate ]
                             │  (Total stack height Z = 70 mm, Yaw = +90°)
                             ▼
       [ End-Effector: Tesollo DG-5F Right Hand (rl_dg_base_link) ]
```

> [!WARNING]
> **Critical Mechanical Rule:** Any operator guidance handle or mounting adapter must be mounted **downstream** of the OnRobot HEX-E v2 sensing element. Anything mounted upstream (directly on the UR5e flange) bypasses the strain gauges and will not be measured.

This exact kinematic and geometric chain is modeled in [`urdf/ur5e_tesollo.urdf.xacro`](../urdf/ur5e_tesollo.urdf.xacro) and [`launch/dg5f_rsp.launch.py`](../launch/dg5f_rsp.launch.py).

---

## 4. Electrical Wiring & Power Supplies

| Device | Required Power Supply | Wiring Details |
| :--- | :--- | :--- |
| **OnRobot HEX-E v2** | **24 V DC external (mandatory)** | **No PoE.** Powered via the dedicated 24V DC junction box (screw the circular M8/M12 sensor connector, plug the 24V DC mains adapter, and switch on). |
| **Tesollo DG-5F-R** | **24 V DC external (5A)** | Dedicated 24V DC power supply connected to the hand's power distribution cable. |
| **Xela uSkin Tactile** | **5 V USB + USB-CAN** | Two USB cables: one 5V USB power cable (blue indicator LED) and one VSCOM USB-CAN adapter (`/dev/ttyUSB0` -> `slcan0` at 1 Mbps). |
| **UR5e Robotic Arm** | **230 V AC mains** | Standard Universal Robots e-Series Control Box. |

---

## 5. Network Interface Configuration on the Control PC

| Device | PC Interface | Protocol | OSI Layer | PC IP Configuration | Target Device Address |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UR5e Arm** | `enp2s0` (via Router) | TCP/IP (RTDE) | Layer 3 | `192.168.3.10/24` | `192.168.3.101` |
| **Tesollo DG-5F** | `enp2s0` (via Router) | Modbus TCP | Layer 3 | `169.254.186.10/16` | `169.254.186.72:502` |
| **OnRobot HEX-E v2** | `enxe4fac4b94578` | **EtherCAT (CoE)** | **Layer 2 Raw** | **NO IP ADDRESS** | EtherCAT Slave `#1` |

### Low-Level EtherCAT Port Preparation (TP-Link USB-Ethernet Adapter)

EtherCAT on Linux operates over raw `AF_PACKET` sockets via `pysoem`. To eliminate packet jitter and prevent `NetworkManager` from disrupting the link with DHCP requests:

```bash
# 1. Prevent NetworkManager from managing the dedicated EtherCAT interface
sudo nmcli device set enxe4fac4b94578 managed no

# 2. Bring the physical link UP (without assigning an IPv4/IPv6 address)
sudo ip link set enxe4fac4b94578 up

# 3. Disable interrupt coalescing for minimal latency
sudo ethtool -C enxe4fac4b94578 rx-usecs 0 tx-usecs 0

# 4. Disable hardware offloading (GRO, GSO, TSO)
sudo ethtool -K enxe4fac4b94578 gro off gso off tso off

# 5. Verify physical link detection
sudo ethtool enxe4fac4b94578 | grep "Link detected"
```

---

## 6. Software Tare & Static Offset Compensation

At rest, the OnRobot HEX-E v2 supports the suspended mass of the mechanical adapter plate and the Tesollo DG-5F hand (~2.04 kg payload), and exhibits an unloaded static Z-axis baseline offset.

The acquisition script [`scripts/test_onrobot_ft.py`](../scripts/test_onrobot_ft.py) automatically performs a **100-sample software tare** at startup (averaging forces $F_x, F_y, F_z$ and torques $T_x, T_y, T_z$ at rest) and records both **tared** and **raw** 6-axis measurements alongside their Euclidean norms $\|\mathbf{F}\|$ and $\|\mathbf{T}\|$.

---

*Author: Kamil BENMADI (<kamil.benmadi@sigma-clermont.fr>) — [GitHub](https://github.com/1000K-sudo) | [LinkedIn](https://www.linkedin.com/in/kamilb-)*
