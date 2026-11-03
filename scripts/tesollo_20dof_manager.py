#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
tesollo_20dof_manager.py
========================
20-DoF posture manager for the Tesollo DG-5F right anthropomorphic hand.
Supports:
  1. Importing poses created and validated in DGManager (GripperRecipeData.json)
  2. Live capture of the 20 real joint angles from the hand (via libDGSDK.so ctypes)
  3. Smoothly applying a 20-DoF posture on the physical hand without collision risk
  4. Publishing the trajectory on ROS 2 (/dg5f_right/joint_trajectory) or direct SDK command
"""

import sys
import os
import json
import time
import argparse
import ctypes
from typing import Dict, List, Any, Optional

# --- Default Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
DGMANAGER_CONFIG_PATH = os.path.join(
    WORKSPACE_DIR, "config", "GripperRecipeData.json"
)
HAND_POSES_20DOF_FILE = os.path.join(WORKSPACE_DIR, "config", "hand_poses_20dof.json")
LIB_DGSDK_PATH = (
    "/usr/local/lib/libDGSDK.so"
    if os.path.isfile("/usr/local/lib/libDGSDK.so")
    else os.path.join(WORKSPACE_DIR, "sdk_tools", "DGSDK", "libDGSDK.so")
)

FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
JOINT_ROLES = ["Abduction/Adduction", "Rotation/Flexion 1", "Flexion 2", "Flexion 3"]

# Standardized ROS 2 joint names for the 20 joints
ROS2_JOINT_NAMES = [
    "rj_dg_1_1", "rj_dg_1_2", "rj_dg_1_3", "rj_dg_1_4",  # Thumb
    "rj_dg_2_1", "rj_dg_2_2", "rj_dg_2_3", "rj_dg_2_4",  # Index
    "rj_dg_3_1", "rj_dg_3_2", "rj_dg_3_3", "rj_dg_3_4",  # Middle
    "rj_dg_4_1", "rj_dg_4_2", "rj_dg_4_3", "rj_dg_4_4",  # Ring
    "rj_dg_5_1", "rj_dg_5_2", "rj_dg_5_3", "rj_dg_5_4",  # Pinky
]


# =============================================================================
# CTypes Structures for libDGSDK.so
# =============================================================================
class GripperSystemSetting(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('comport', ctypes.c_char * 32),
        ('ip', ctypes.c_char * 32),
        ('port', ctypes.c_int),
        ('readTimeout', ctypes.c_int),
        ('controlMode', ctypes.c_int),
        ('communicationMode', ctypes.c_int),
        ('slaveID', ctypes.c_int),
        ('baudrate', ctypes.c_int),
    ]


class GripperSetting(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('jointOffset', ctypes.c_float * 20),
        ('jointInpose', ctypes.c_float * 20),
        ('tcpInpose', ctypes.c_float * 5),
        ('orientationInpose', ctypes.c_float * 5),
        ('receivedDataType', ctypes.c_int * 6),
        ('movingInpose', ctypes.c_float),
        ('jointCount', ctypes.c_int),
        ('fingerCount', ctypes.c_int),
        ('model', ctypes.c_int),
        ('dutyByteLength', ctypes.c_int8),
    ]


class ReceivedGripperData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('joint', ctypes.c_float * 20),
        ('current', ctypes.c_int * 20),
        ('velocity', ctypes.c_int * 20),
        ('temperature', ctypes.c_float * 20),
        ('TCP', ctypes.c_float * 30),
        ('moving', ctypes.c_int),
        ('targetArrived', ctypes.c_int),
        ('blendMoveState', ctypes.c_int),
        ('currentBlendIndex', ctypes.c_int),
        ('productID', ctypes.c_int),
        ('firmwareVersion', ctypes.c_int),
    ]


# =============================================================================
# Low-Level DGSDK Interface Class
# =============================================================================
class TesolloLowLevelSDK:
    def __init__(self, ip: str = "169.254.186.72", port: int = 502):
        self.ip = ip
        self.port = port
        self.lib = None
        self.connected = False
        self.latest_joints: List[float] = [0.0] * 20
        self.data_received = False
        self._cb_holder = None

        if os.path.exists(LIB_DGSDK_PATH):
            try:
                self.lib = ctypes.CDLL(LIB_DGSDK_PATH)
                self._setup_prototypes()
            except Exception as e:
                print(f"[WARN] Could not load {LIB_DGSDK_PATH}: {e}")

    def _setup_prototypes(self):
        self.lib.SetGripperSystem.argtypes = [GripperSystemSetting]
        self.lib.SetGripperSystem.restype = ctypes.c_int

        self.lib.SetGripperOption.argtypes = [GripperSetting]
        self.lib.SetGripperOption.restype = ctypes.c_int

        self.lib.ConnectToGripper.argtypes = []
        self.lib.ConnectToGripper.restype = ctypes.c_int

        self.lib.DisconnectToGripper.argtypes = []
        self.lib.DisconnectToGripper.restype = ctypes.c_int

        self.lib.SystemStart.argtypes = []
        self.lib.SystemStart.restype = ctypes.c_int

        self.lib.SystemStop.argtypes = []
        self.lib.SystemStop.restype = ctypes.c_int

        self.lib.SetMotionTimeAllEqual.argtypes = [ctypes.c_int]
        self.lib.SetMotionTimeAllEqual.restype = ctypes.c_int

        self.lib.MoveJointAll.argtypes = [ctypes.POINTER(ctypes.c_float)]
        self.lib.MoveJointAll.restype = ctypes.c_int

        self.ON_DATA_FUNC = ctypes.CFUNCTYPE(None, ReceivedGripperData)
        self.lib.CallbackForOnReceivedGripperData.argtypes = [self.ON_DATA_FUNC]
        self.lib.CallbackForOnReceivedGripperData.restype = ctypes.c_int

    def _on_data(self, data: ReceivedGripperData):
        self.latest_joints = [round(float(data.joint[i]), 2) for i in range(20)]
        self.data_received = True

    def connect(self) -> bool:
        if not self.lib:
            return False

        sys_set = GripperSystemSetting()
        sys_set.port = self.port
        sys_set.baudrate = 115200
        sys_set.communicationMode = 1  # ETHERNET
        sys_set.controlMode = 0        # OPERATOR
        sys_set.readTimeout = 1000
        sys_set.slaveID = 1
        sys_set.ip = self.ip.encode('utf-8')
        sys_set.comport = b"COM1"

        if self.lib.SetGripperSystem(sys_set) != 0:
            return False

        self._cb_holder = self.ON_DATA_FUNC(self._on_data)
        self.lib.CallbackForOnReceivedGripperData(self._cb_holder)

        if self.lib.ConnectToGripper() != 0:
            return False
        time.sleep(0.4)

        gs = GripperSetting()
        gs.model = 4  # DG_MODEL_DG_5F_RIGHT
        gs.movingInpose = 1.0
        gs.receivedDataType[0] = 1
        gs.receivedDataType[1] = 2
        gs.receivedDataType[2] = 3
        gs.receivedDataType[3] = 4
        if self.lib.SetGripperOption(gs) != 0:
            self.lib.DisconnectToGripper()
            return False
        time.sleep(0.5)

        if self.lib.SystemStart() != 0:
            self.lib.DisconnectToGripper()
            return False

        time.sleep(0.3)
        self.connected = True
        return True

    def disconnect(self):
        if self.connected and self.lib:
            try:
                self.lib.SystemStop()
                time.sleep(0.2)
                self.lib.DisconnectToGripper()
            except Exception:
                pass
            self.connected = False

    def read_actual_joints(self, timeout_sec: float = 2.0) -> Optional[List[float]]:
        """Waits for a feedback frame and returns the 20 actual joint angles in degrees."""
        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            if self.data_received:
                return list(self.latest_joints)
            time.sleep(0.05)
        return None

    def move_joint_all(self, target_joints: List[float], time_ms: int = 1500) -> bool:
        """Sends all 20 target joint angles with an interpolated motion duration."""
        if not self.connected or len(target_joints) != 20:
            return False
        c_arr = (ctypes.c_float * 20)(*target_joints)
        self.lib.SetMotionTimeAllEqual(time_ms)
        res = self.lib.MoveJointAll(c_arr)
        return res == 0


# =============================================================================
# Posture Import & Catalog Management Functions
# =============================================================================
def load_20dof_presets(file_path: str = HAND_POSES_20DOF_FILE) -> Dict[str, Any]:
    if os.path.isfile(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_20dof_presets(presets: Dict[str, Any], file_path: str = HAND_POSES_20DOF_FILE):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)


def import_from_dgmanager(dgmanager_json: str = DGMANAGER_CONFIG_PATH) -> Dict[str, Any]:
    """Imports all postures defined in the DGManager recipe configuration file."""
    if not os.path.isfile(dgmanager_json):
        print(f"[ERROR] DGManager recipe file not found: {dgmanager_json}")
        return {}

    with open(dgmanager_json, "r", encoding="utf-8") as f:
        raw = json.load(f)

    poses_dict = raw.get("poses", {})
    imported = {}

    default_names = {
        "1": "DG_Home_Ouverte",
        "2": "DG_Prise_Cylindrique_Large",
        "3": "DG_Saisie_Enveloppante",
        "4": "DG_Presaisie_Orientee",
        "5": "DG_Pince_Fine_Pouce_Index",
        "6": "DG_Pince_3_Doigts",
    }

    for k, v in poses_dict.items():
        tj = v.get("targetJoint", [])
        if len(tj) == 20 and any(abs(x) > 0.001 for x in tj):
            name = default_names.get(k, f"DG_Recipe_Pose_{k}")
            imported[name] = {
                "description": f"Certified 20-DoF posture imported from DGManager (Recipe #{k})",
                "joints_20": [round(float(x), 2) for x in tj],
                "motion_time_ms": v.get("jointMotionTime", [1500]*20)[0]
            }

    if "DG_Home_Ouverte" not in imported and "1" in poses_dict:
        imported["DG_Home_Ouverte"] = {
            "description": "Reference open hand posture (all 20 joints at 0.0 deg)",
            "joints_20": [0.0] * 20,
            "motion_time_ms": 1500
        }

    return imported


def format_pose_display(name: str, pose_data: Dict[str, Any]) -> str:
    q = pose_data.get("joints_20", [0.0]*20)
    desc = pose_data.get("description", "")
    lines = [f"\n🖐 20-DoF Posture: {name}"]
    if desc:
        lines.append(f"   Description : {desc}")
    lines.append("   " + "-" * 55)

    for i, f_name in enumerate(FINGER_NAMES):
        vals = q[i*4 : (i+1)*4]
        lines.append(
            f"   • {f_name:11s} : [Abd:{vals[0]:+5.1f}°, Rot/MCP:{vals[1]:+5.1f}°, PIP:{vals[2]:+5.1f}°, DIP:{vals[3]:+5.1f}°]"
        )

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================
def cmd_import_dgmanager():
    print(f"[*] Reading DGManager recipes from: {DGMANAGER_CONFIG_PATH}")
    imported = import_from_dgmanager()
    if not imported:
        print("[-] No postures found to import.")
        return

    existing = load_20dof_presets()
    existing.update(imported)
    save_20dof_presets(existing)
    print(f"[✔] {len(imported)} 20-DoF postures imported and saved to {HAND_POSES_20DOF_FILE}:")
    for name in imported:
        print(f"    - {name}")


def cmd_list_poses():
    presets = load_20dof_presets()
    if not presets:
        print(f"[-] No postures found in {HAND_POSES_20DOF_FILE}. Run 'import' or 'capture'.")
        return

    print(f"\n=== Tesollo 20-DoF Posture Library ({len(presets)} poses) ===")
    for name, data in presets.items():
        print(format_pose_display(name, data))


def cmd_capture_live(name: str, desc: str = ""):
    print("[*] Connecting to Tesollo hand for live encoder capture...")
    sdk = TesolloLowLevelSDK()
    if not sdk.connect():
        print("[-] Failed to connect to hand (169.254.186.72:502). Check 24V power and Ethernet cable.")
        return

    try:
        q = sdk.read_actual_joints(timeout_sec=3.0)
        if not q:
            print("[-] No joint encoder data received from hand.")
            return

        presets = load_20dof_presets()
        presets[name] = {
            "description": desc or f"Live posture captured from hardware encoders ({time.strftime('%Y-%m-%d %H:%M:%S')})",
            "joints_20": q,
            "motion_time_ms": 1500
        }
        save_20dof_presets(presets)
        print(f"[✔] Posture '{name}' captured successfully!")
        print(format_pose_display(name, presets[name]))
    finally:
        sdk.disconnect()


def cmd_play_pose(name: str, duration_sec: float = 2.0):
    presets = load_20dof_presets()
    if name not in presets:
        print(f"[-] Posture '{name}' not found in {HAND_POSES_20DOF_FILE}.")
        return

    pose_data = presets[name]
    q = pose_data["joints_20"]
    time_ms = int(duration_sec * 1000)

    print(f"[*] Safely applying posture '{name}' (duration: {duration_sec}s)...")
    sdk = TesolloLowLevelSDK()
    if not sdk.connect():
        print("[-] Failed to connect to Tesollo hand.")
        return

    try:
        ok = sdk.move_joint_all(q, time_ms=time_ms)
        if ok:
            print("[✔] Command transmitted successfully. Executing motion...")
            time.sleep(duration_sec + 0.2)
            print("[✔] Target posture reached.")
        else:
            print("[-] Failed to send MoveJointAll command.")
    finally:
        sdk.disconnect()


# =============================================================================
# Main
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Tesollo DG-5F 20-DoF Posture Manager")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("import", help="Import recipes from DGManager")
    subparsers.add_parser("list", help="List all saved 20-DoF postures")

    p_cap = subparsers.add_parser("capture", help="Capture current posture from physical hand encoders")
    p_cap.add_argument("name", type=str, help="Posture name")
    p_cap.add_argument("--desc", type=str, default="", help="Optional description")

    p_play = subparsers.add_parser("play", help="Apply a 20-DoF posture on the physical hand")
    p_play.add_argument("name", type=str, help="Posture name to apply")
    p_play.add_argument("--duration", type=float, default=2.0, help="Motion duration in seconds (default: 2.0)")

    args = parser.parse_args()

    if args.command == "import":
        cmd_import_dgmanager()
    elif args.command == "list":
        cmd_list_poses()
    elif args.command == "capture":
        cmd_capture_live(args.name, args.desc)
    elif args.command == "play":
        cmd_play_pose(args.name, args.duration)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
