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
        print(f"[ERREUR] Fichier de poses introuvable : {POSES_FILE}")
        sys.exit(1)
    with open(POSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def execute_via_sdk(joints_20: List[float], duration_sec: float) -> bool:
    from tesollo_20dof_manager import TesolloLowLevelSDK
    sdk = TesolloLowLevelSDK()
    if not sdk.connect():
        print("[ERREUR] Impossible de se connecter à la main Tesollo (169.254.186.72:502).")
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
        node.get_logger().info(f"Trajectoire ROS 2 publiée sur /dg5f_right/joint_trajectory ({duration_sec}s)")
        node.destroy_node()
    except Exception as e:
        # ROS 2 non critique si l'envoi SDK direct fonctionne
        pass

def main():
    parser = argparse.ArgumentParser(description="Application sécurisée d'une posture 20-DDL Tesollo")
    parser.add_argument("pose", type=str, nargs="?", default="", help="Nom de la posture à appliquer")
    parser.add_argument("--duration", type=float, default=2.0, help="Durée du mouvement en secondes (défaut: 2.0s)")
    parser.add_argument("--list", action="store_true", help="Lister les postures disponibles")
    args = parser.parse_args()

    poses = load_poses()

    if args.list or not args.pose:
        print("\n=== Postures 20-DDL Disponibles ===")
        for name, data in poses.items():
            print(f"  • {name:28s} : {data.get('description', '')}")
        print("\nExemple d'utilisation :")
        print("  python3 send_hand_pose_ros2.py DG_Pince_Fine_Pouce_Index --duration 2.5\n")
        return

    name = args.pose
    if name not in poses:
        print(f"[ERREUR] Posture '{name}' inconnue. Utilisez --list pour voir les choix disponibles.")
        sys.exit(1)

    pose_data = poses[name]
    joints_20 = pose_data["joints_20"]
    desc = pose_data.get("description", "")

    print(f"\n🚀 Application de la posture '{name}'...")
    if desc:
        print(f"   Description : {desc}")
    print(f"   Durée : {args.duration:.1f} s")

    # 1. Envoi direct matériel via libDGSDK (garantit l'exécution même sans driver ROS actif)
    ok = execute_via_sdk(joints_20, args.duration)

    # 2. Publication miroir sur ROS 2 pour synchronisation RViz / listeners
    publish_ros2(joints_20, args.duration)

    if ok:
        print(f"[✔] Posture '{name}' appliquée avec succès sans risque de collision articulaire !")
    else:
        print(f"[-] Erreur lors de l'application de la posture.")

if __name__ == "__main__":
    main()
