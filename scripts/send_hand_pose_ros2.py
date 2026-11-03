#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
send_hand_pose_ros2.py
======================
Standalone ROS 2 / Python script to apply a certified 20-DoF posture on the Tesollo DG-5F hand.
Supports sending the posture:
  1. Directly via libDGSDK.so (high-reliability native Modbus TCP)
  2. And/or by publishing a JointTrajectory message on ROS 2 topics (/dg5f_right/joint_trajectory)

Usage:
  python3 scripts/send_hand_pose_ros2.py DG_Pince_Fine_Pouce_Index --duration 2.0
  python3 scripts/send_hand_pose_ros2.py DG_Home_Ouverte
  python3 scripts/send_hand_pose_ros2.py --list
"""

import sys
import os
import json
import math
import argparse
from typing import Dict, List, Any

# 20-DoF postures catalog path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
POSES_FILE = os.path.join(WORKSPACE_DIR, "config", "hand_poses_20dof.json")

ROS2_JOINT_NAMES = [
    "rj_dg_1_1", "rj_dg_1_2", "rj_dg_1_3", "rj_dg_1_4",
    "rj_dg_2_1", "rj_dg_2_2", "rj_dg_2_3", "rj_dg_2_4",
    "rj_dg_3_1", "rj_dg_3_2", "rj_dg_3_3", "rj_dg_3_4",
    "rj_dg_4_1", "rj_dg_4_2", "rj_dg_4_3", "rj_dg_4_4",
    "rj_dg_5_1", "rj_dg_5_2", "rj_dg_5_3", "rj_dg_5_4",
]


def load_poses() -> Dict[str, Any]:
    if not os.path.isfile(POSES_FILE):
        print(f"[ERROR] Postures file not found: {POSES_FILE}")
        sys.exit(1)
    with open(POSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_via_sdk(joints_20: List[float], duration_sec: float) -> bool:
    from tesollo_20dof_manager import TesolloLowLevelSDK
    sdk = TesolloLowLevelSDK()
    if not sdk.connect():
        print("[ERROR] Unable to connect to Tesollo hand (169.254.186.72:502).")
        return False
    try:
        time_ms = int(duration_sec * 1000)
        return sdk.move_joint_all(joints_20, time_ms=time_ms)
    finally:
        sdk.disconnect()


def publish_ros2(joints_20: List[float], duration_sec: float):
    try:
        import rclpy
        from rclpy.node import Node
        from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
        from builtin_interfaces.msg import Duration

        if not rclpy.ok():
            rclpy.init()

        node = Node("tesollo_pose_sender")
        pub = node.create_publisher(JointTrajectory, "/dg5f_right/joint_trajectory", 10)

        traj = JointTrajectory()
        traj.joint_names = ROS2_JOINT_NAMES
        traj.header.stamp = node.get_clock().now().to_msg()

        point = JointTrajectoryPoint()
        point.positions = [math.radians(deg) for deg in joints_20]
        point.velocities = [0.0] * 20
        sec = int(duration_sec)
        nanosec = int((duration_sec - sec) * 1e9)
        point.time_from_start = Duration(sec=sec, nanosec=nanosec)

        traj.points = [point]
        pub.publish(traj)
        node.get_logger().info(f"ROS 2 JointTrajectory published on /dg5f_right/joint_trajectory ({duration_sec}s)")
        node.destroy_node()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Safe execution of a certified 20-DoF Tesollo posture")
    parser.add_argument("pose", type=str, nargs="?", default="", help="Name of the posture to apply")
    parser.add_argument("--duration", type=float, default=2.0, help="Motion duration in seconds (default: 2.0s)")
    parser.add_argument("--list", action="store_true", help="List available 20-DoF postures")
    args = parser.parse_args()

    poses = load_poses()

    if args.list or not args.pose:
        print("\n=== Available 20-DoF Postures ===")
        for name, data in poses.items():
            print(f"  • {name:28s} : {data.get('description', '')}")
        print("\nUsage example:")
        print("  ./ur5e_cell.sh poses DG_Pince_Fine_Pouce_Index --duration 2.5\n")
        sys.exit(0)

    if args.pose not in poses:
        print(f"[ERROR] Unknown posture '{args.pose}'. Available postures:")
        for name in poses:
            print(f"  - {name}")
        sys.exit(1)

    pose_data = poses[args.pose]
    joints_20 = pose_data["joints_20"]

    print(f"[*] Applying 20-DoF posture '{args.pose}' ({args.duration}s)...")
    print(f"    Description : {pose_data.get('description', '')}")

    publish_ros2(joints_20, args.duration)
    ok = execute_via_sdk(joints_20, args.duration)
    if ok:
        print(f"[✔] Posture '{args.pose}' applied successfully on Tesollo DG-5F hand.")
    else:
        print("[!] Direct SDK execution failed (verify hand power and Ethernet link).")


if __name__ == "__main__":
    main()
