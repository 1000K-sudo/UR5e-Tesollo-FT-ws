#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
test_combined_motion.py
=======================
Safe coordinated motion test script:
  - Universal Robots UR5e arm (gentle relative rotation on wrist_3_joint)
  - Tesollo DG-5F anthropomorphic hand (synchronized 5-finger closing / opening)

Safety:
  - Reads the ACTUAL current joint state of the UR5e before issuing any command.
  - Minimal relative motion (+/- 8.5 degrees on wrist_3_joint only).
  - Slow speed and smooth acceleration (trajectory interpolated over 5 seconds).
  - Requires explicit [ENTER] operator confirmation before starting.
"""

import sys
import time
import math
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Duration


def deg2rad(d):
    return d * math.pi / 180.0


class CombinedMotionTester(Node):
    def __init__(self):
        super().__init__('combined_motion_tester')

        # Noms des articulations UR5e
        self.ur_joint_names = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint",
        ]

        # Noms des 20 articulations Tesollo DG-5F (doigts 1 à 5)
        self.tesollo_joint_names = [
            "rj_dg_1_1", "rj_dg_1_2", "rj_dg_1_3", "rj_dg_1_4",  # Pouce
            "rj_dg_2_1", "rj_dg_2_2", "rj_dg_2_3", "rj_dg_2_4",  # Index
            "rj_dg_3_1", "rj_dg_3_2", "rj_dg_3_3", "rj_dg_3_4",  # Majeur
            "rj_dg_4_1", "rj_dg_4_2", "rj_dg_4_3", "rj_dg_4_4",  # Annulaire
            "rj_dg_5_1", "rj_dg_5_2", "rj_dg_5_3", "rj_dg_5_4",  # Auriculaire
        ]

        # Publishers
        self.ur_pub = self.create_publisher(
            JointTrajectory,
            '/scaled_joint_trajectory_controller/joint_trajectory',
            10
        )
        self.hand_pub = self.create_publisher(
            JointTrajectory,
            '/dg5f_right/dg5f_right_controller/joint_trajectory',
            10
        )

        # Subscriber pour capturer la position actuelle de l'UR5e
        self.current_ur_positions = {}
        self.ur_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_states_callback,
            10
        )

        self.get_logger().info("En attente de la réception des états articulaires de l'UR5e (/joint_states)...")

    def joint_states_callback(self, msg: JointState):
        for name, pos in zip(msg.name, msg.position):
            if name in self.ur_joint_names:
                self.current_ur_positions[name] = pos

    def wait_for_ur_state(self, timeout_sec=5.0):
        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            rclpy.spin_once(self, timeout_sec=0.1)
            if all(j in self.current_ur_positions for j in self.ur_joint_names):
                return True
        return False

    def build_ur_trajectory(self):
        """Génère un va-et-vient doux sur le poignet wrist_3 (+/- 8.5 deg) en 5s."""
        traj = JointTrajectory()
        traj.joint_names = self.ur_joint_names
        traj.header.stamp = self.get_clock().now().to_msg()

        q0 = [self.current_ur_positions[j] for j in self.ur_joint_names]
        delta_wrist = deg2rad(8.5)  # 0.148 rad

        # Point 1 : Légère rotation wrist_3 (t = 2.5s)
        p1 = JointTrajectoryPoint()
        q1 = list(q0)
        q1[5] += delta_wrist  # index 5 = wrist_3_joint
        p1.positions = q1
        p1.velocities = [0.0] * 6
        p1.time_from_start = Duration(sec=2, nanosec=500_000_000)

        # Point 2 : Retour exact à la position d'origine (t = 5s)
        p2 = JointTrajectoryPoint()
        p2.positions = list(q0)
        p2.velocities = [0.0] * 6
        p2.time_from_start = Duration(sec=5, nanosec=0)

        traj.points = [p1, p2]
        return traj

    def build_hand_trajectory(self):
        """Génère une fermeture souple des 4 doigts + pouce, puis réouverture en 5s."""
        traj = JointTrajectory()
        traj.joint_names = self.tesollo_joint_names

        # Position ouverte (repos = 0)
        q_open = [0.0] * 20

        # Position préhension (flexion à 60° des phalanges médianes et distales)
        flex = deg2rad(60.0)
        q_closed = [
            0.0, deg2rad(25.0), flex, flex,  # Pouce
            0.0, 0.0, flex, flex,            # Index
            0.0, 0.0, flex, flex,            # Majeur
            0.0, 0.0, flex, flex,            # Annulaire
            0.0, 0.0, flex, flex,            # Auriculaire
        ]

        # Point 0 : Main ouverte (t = 0s)
        p0 = JointTrajectoryPoint()
        p0.positions = q_open
        p0.time_from_start = Duration(sec=0, nanosec=0)

        # Point 1 : Main fermée synchronisée avec la mi-course du bras (t = 2.5s)
        p1 = JointTrajectoryPoint()
        p1.positions = q_closed
        p1.time_from_start = Duration(sec=2, nanosec=500_000_000)

        # Point 2 : Réouverture complète (t = 5s)
        p2 = JointTrajectoryPoint()
        p2.positions = q_open
        p2.time_from_start = Duration(sec=5, nanosec=0)

        traj.points = [p0, p1, p2]
        return traj

    def execute_motion(self):
        import subprocess
        import threading
        import os

        ur_traj = self.build_ur_trajectory()
        hand_traj = self.build_hand_trajectory()
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmd_path = os.path.join(workspace_root, "sdk_tools", "build", "tesollo_cmd")
        if not os.path.isfile(cmd_path):
            cmd_path = os.path.join(workspace_root, "sdk_tools", "tesollo_cmd")

        def trigger_hand():
            if os.path.isfile(cmd_path):
                self.get_logger().info("[Main Tesollo] Exécution physique du mouvement (Flexion 45° puis réouverture)...")
                # Flexion des doigts
                subprocess.run([cmd_path, "flex", "45"])
                time.sleep(1.0)
                # Retour à zéro
                subprocess.run([cmd_path, "zero"])
            else:
                self.get_logger().warn("[Main Tesollo] Utilitaire tesollo_cmd non trouvé, publication topic ROS2 uniquement.")

        self.get_logger().info(">>> ENVOI SIMULTANÉ DES TRAJECTOIRES BRAS + MAIN <<<")

        # 1. Démarrer la main dans un thread dédié
        hand_thread = threading.Thread(target=trigger_hand)
        hand_thread.start()

        # 2. Envoyer la trajectoire au bras UR5e et sur le topic ROS 2
        self.ur_pub.publish(ur_traj)
        self.hand_pub.publish(hand_traj)
        self.get_logger().info("Mouvement coordonné en cours (durée totale : ~5 secondes)...")

        t0 = time.time()
        while time.time() - t0 < 5.5:
            rclpy.spin_once(self, timeout_sec=0.1)

        hand_thread.join(timeout=3.0)
        self.get_logger().info("Mouvement terminé avec succès !")


def main():
    rclpy.init()
    tester = CombinedMotionTester()

    print("\n" + "=" * 70)
    print("  TEST DE MOUVEMENT COMBINÉ SÉCURISÉ : UR5e + TESOLLO DG-5F")
    print("=" * 70)

    # 1. Attente de la capture d'état
    if not tester.wait_for_ur_state(timeout_sec=5.0):
        print("\n[ERREUR] Impossible de lire /joint_states du robot UR5e.")
        print("Vérifiez que ur_robot_driver est bien lancé et que le programme")
        print("URCap 'External Control' est démarré sur le Teach Pendant.")
        tester.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    print("\nPositions articulaires actuelles de l'UR5e capturées avec succès :")
    for j in tester.ur_joint_names:
        pos_deg = math.degrees(tester.current_ur_positions[j])
        print(f"  - {j:20s} : {pos_deg:+8.2f}° ({tester.current_ur_positions[j]:+.4f} rad)")

    print("\nPlan de mouvement prévu :")
    print("  1. Bras UR5e  : rotation douce relative de +8.5° sur wrist_3, puis retour à la position initiale.")
    print("  2. Main DG-5F : fermeture coordonnée des 5 doigts à mi-course, puis réouverture complète.")
    print("  3. Durée totale : 5.0 secondes (vitesse très modérée).")
    print("=" * 70)
    print("\n[CONSIGNE DE SÉCURITÉ]")
    print("  - Gardez le bouton d'arrêt d'urgence (Coup de poing) du Teach Pendant à portée de main.")
    print("  - Vérifiez qu'aucun obstacle ne se trouve à proximité immédiate de la main.")

    try:
        input("\nAppuyez sur [ENTRÉE] pour exécuter le mouvement (ou Ctrl+C pour annuler)... ")
    except KeyboardInterrupt:
        print("\nAnnulé par l'utilisateur.")
        tester.destroy_node()
        rclpy.shutdown()
        sys.exit(0)

    tester.execute_motion()
    tester.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
