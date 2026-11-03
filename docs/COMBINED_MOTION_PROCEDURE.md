<!-- 
==============================================================================
Author: Kamil BENMADI
Email: kamil.benmadi@sigma-clermont.fr
GitHub: https://github.com/1000K-sudo
LinkedIn: https://www.linkedin.com/in/kamilb-
==============================================================================
-->

# Operating Procedure: Coordinated UR5e Arm + Tesollo DG-5F Hand + OnRobot HEX-E v2 Sensor

This document describes the step-by-step multi-terminal procedure to initialize the ROS 2 drivers, execute a **safe, synchronized motion** between the **UR5e** robotic arm and the **Tesollo DG-5F** dexterous hand, and record real-time 6-axis force/torque measurements from the **OnRobot HEX-E v2** sensor.

---

## 1. Essential Safety Guidelines

> [!CAUTION]
> - **Emergency Stop:** Keep the red E-Stop mushroom button on the UR5e Teach Pendant within immediate reach at all times.
> - **Workspace Clearance:** Ensure the full sweep volume of the UR5e arm and Tesollo hand is clear of obstacles.
> - **Speed Scaling:** Set the PolyScope speed slider on the Teach Pendant to **30% maximum** during initial testing.

---

## 2. Teach Pendant Prerequisites (UR5e PolyScope)

Before launching software nodes on the workstation PC:
1. Power on the UR5e control box and release the brakes (**ON / Start** in PolyScope $\rightarrow$ green status `Robotmode: RUNNING`).
2. Verify that the active payload is configured to **2.04 kg** (accounting for the OnRobot HEX-E v2 sensor, adapter flange, and Tesollo DG-5F hand).
3. Switch PolyScope to **Remote Control** mode (top-right remote icon) or load the **External Control** URCap program pointing to the workstation IP (`192.168.3.10`, port `50002`).

---

## 3. Multi-Terminal Execution Workflow

### Terminal 1 — UR5e ROS 2 Driver & RViz2 Visualization

Launch the official Universal Robots ROS 2 driver and open RViz2:

```bash
./ur5e_cell.sh ur5e
# Equivalent raw command:
# ros2 launch ur_robot_driver ur5e.launch.py robot_ip:=192.168.3.101 launch_rviz:=true
```

Once the driver reports waiting for connection, press **Play (▶)** on the UR5e Teach Pendant. The terminal will display:
`Robot connected to reverse interface. Ready to receive control commands.`

---

### Terminal 2 — Tesollo DG-5F 20-DoF TF & Joint State Broadcaster (Optional for Full 3D RViz)

To visualize the 20 finger joints of the Tesollo hand attached to the UR5e flange (`tool0`) in real time inside RViz2:

```bash
./ur5e_cell.sh hand_rsp &
./ur5e_cell.sh hand_broadcaster
```

---

### Terminal 3 — Synchronized UR5e + Tesollo Motion Execution

Run [`scripts/test_combined_motion.py`](../scripts/test_combined_motion.py) to read the current actual joint state of the UR5e arm and execute a coordinated 5-second trajectory:

```bash
./ur5e_cell.sh combined_test
# Equivalent raw command:
# python3 scripts/test_combined_motion.py
```

**Motion Sequence (~5.0 seconds total):**
1. **UR5e Arm:** Performs a smooth, relative rotation of **$+8.5^\circ$ on `wrist_3_joint`** over $2.5\text{ s}$, then returns to its exact initial posture at $t = 5.0\text{ s}$. All other arm joints remain locked at their current angles.
2. **Tesollo DG-5F Hand:** Simultaneously flexes all 5 fingers to $45^\circ$ (via `tesollo_cmd` and `/dg5f_right/dg5f_right_controller/joint_trajectory`), holds the grasp, and reopens to $0^\circ$.
3. Requires explicit `[ENTER]` operator confirmation before any motion begins.

---

### Terminal 4 — Real-Time 100 Hz Force/Torque Recording (OnRobot HEX-E v2)

To record the inertial and manipulation forces/torques generated during the movement:

```bash
./ur5e_cell.sh ft_acquire --format all
# Equivalent raw command:
# sudo python3 scripts/test_onrobot_ft.py --iface enxe4fac4b94578 --format all
```

- Start the acquisition **before** pressing `[ENTER]` in Terminal 3.
- Press `Ctrl+C` at the end of the motion to automatically export `.csv`, `.txt`, and `.npy` logs into [`data/onrobot_ft_recordings/`](../data/onrobot_ft_recordings/).
- Plot the triaxial components and Euclidean norms ($\|\mathbf{F}\|$, $\|\mathbf{T}\|$):
  ```bash
  ./ur5e_cell.sh ft_plot --latest
  ```

---

## 4. Testing the Tesollo DG-5F Hand Standalone (`tesollo_cmd`)

The compiled C++ CLI utility [`sdk_tools/tesollo_cmd.cpp`](../sdk_tools/tesollo_cmd.cpp) allows direct low-latency actuation of the hand over Modbus TCP:

```bash
# Move all 20 joints to zero (open hand):
./sdk_tools/build/tesollo_cmd zero

# Flex fingers to a target angle (e.g., 45 deg):
./sdk_tools/build/tesollo_cmd flex 45

# Execute 2-finger precision pinch:
./sdk_tools/build/tesollo_cmd pinch

# Execute index pointing gesture:
./sdk_tools/build/tesollo_cmd point

# Power grasp / release:
./sdk_tools/build/tesollo_cmd grasp
./sdk_tools/build/tesollo_cmd release
```

---

## 5. Quick Troubleshooting

| Symptom | Root Cause | Immediate Fix |
| :--- | :--- | :--- |
| `Robot is not in Remote Control` | Remote control mode is inactive on PolyScope | Tap the remote icon in the top-right bar of the Teach Pendant |
| `Unable to read /joint_states` | External Control URCap program is paused | Press **Play (▶)** on the Teach Pendant |
| Hand does not respond to TCP commands | Link-local subnet missing on `enp2s0` | Run `sudo ip addr add 169.254.186.10/16 dev enp2s0` |
| UR5e Protective Stop | Payload mismatch or external collision | Verify PolyScope payload is set to `2.04 kg` and re-enable arm |

---

*Author: Kamil BENMADI (<kamil.benmadi@sigma-clermont.fr>) — [GitHub](https://github.com/1000K-sudo) | [LinkedIn](https://www.linkedin.com/in/kamilb-)*
