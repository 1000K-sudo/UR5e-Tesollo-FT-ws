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

        # UR5e 6-DoF joint names
        self.ur_joint_names = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint",
        ]

        # Tesollo DG-5F 20-DoF joint names (fingers 1 to 5)
        self.tesollo_joint_names = [
            "rj_dg_1_1", "rj_dg_1_2", "rj_dg_1_3", "rj_dg_1_4",  # Thumb
            "rj_dg_2_1", "rj_dg_2_2", "rj_dg_2_3", "rj_dg_2_4",  # Index
            "rj_dg_3_1", "rj_dg_3_2", "rj_dg_3_3", "rj_dg_3_4",  # Middle
            "rj_dg_4_1", "rj_dg_4_2", "rj_dg_4_3", "rj_dg_4_4",  # Ring
            "rj_dg_5_1", "rj_dg_5_2", "rj_dg_5_3", "rj_dg_5_4",  # Pinky
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

        # Subscriber to capture the current actual posture of the UR5e arm
        self.current_ur_positions = {}
        self.ur_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_states_callback,
            10
        )

        self.get_logger().info("Waiting for UR5e joint states (/joint_states)...")

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
        """Generates a smooth back-and-forth rotation on wrist_3_joint (+/- 8.5 deg) over 5s."""
        traj = JointTrajectory()
        traj.joint_names = self.ur_joint_names
        traj.header.stamp = self.get_clock().now().to_msg()

        q0 = [self.current_ur_positions[j] for j in self.ur_joint_names]
        delta_wrist = deg2rad(8.5)  # 0.148 rad

        # Waypoint 1: Slight wrist_3 rotation (t = 2.5s)
        p1 = JointTrajectoryPoint()
        q1 = list(q0)
        q1[5] += delta_wrist  # index 5 = wrist_3_joint
        p1.positions = q1
        p1.velocities = [0.0] * 6
        p1.time_from_start = Duration(sec=2, nanosec=500_000_000)

        # Waypoint 2: Exact return to initial position (t = 5.0s)
        p2 = JointTrajectoryPoint()
        p2.positions = list(q0)
        p2.velocities = [0.0] * 6
        p2.time_from_start = Duration(sec=5, nanosec=0)

        traj.points = [p1, p2]
        return traj

    def build_hand_trajectory(self):
        """Generates a smooth 5-finger grasp and release over 5s."""
        traj = JointTrajectory()
        traj.joint_names = self.tesollo_joint_names

        q_open = [0.0] * 20

        flex = deg2rad(60.0)
        q_closed = [
            0.0, deg2rad(25.0), flex, flex,  # Thumb
            0.0, 0.0, flex, flex,            # Index
            0.0, 0.0, flex, flex,            # Middle
            0.0, 0.0, flex, flex,            # Ring
            0.0, 0.0, flex, flex,            # Pinky
        ]

        p0 = JointTrajectoryPoint()
        p0.positions = q_open
        p0.time_from_start = Duration(sec=0, nanosec=0)

        p1 = JointTrajectoryPoint()
        p1.positions = q_closed
        p1.time_from_start = Duration(sec=2, nanosec=500_000_000)

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
                self.get_logger().info("[Tesollo Hand] Executing physical finger flexion (45 deg) and release...")
                subprocess.run([cmd_path, "flex", "45"])
                time.sleep(1.0)
                subprocess.run([cmd_path, "zero"])
            else:
                self.get_logger().warn("[Tesollo Hand] tesollo_cmd binary not found; publishing ROS 2 topic only.")

        self.get_logger().info(">>> SENDING SIMULTANEOUS ARM + HAND TRAJECTORIES <<<")

        hand_thread = threading.Thread(target=trigger_hand)
        hand_thread.start()

        self.ur_pub.publish(ur_traj)
        self.hand_pub.publish(hand_traj)
        self.get_logger().info("Coordinated motion in progress (total duration: ~5 seconds)...")

        t0 = time.time()
        while time.time() - t0 < 5.5:
            rclpy.spin_once(self, timeout_sec=0.1)

        hand_thread.join(timeout=3.0)
        self.get_logger().info("Coordinated motion completed successfully!")


def main():
    rclpy.init()
    tester = CombinedMotionTester()

    print("\n" + "=" * 70)
    print("  SAFE COORDINATED MOTION TEST: UR5e + TESOLLO DG-5F")
    print("=" * 70)

    if not tester.wait_for_ur_state(timeout_sec=5.0):
        print("\n[ERROR] Unable to read /joint_states from the UR5e robot.")
        print("Verify that ur_robot_driver is running and that the")
        print("'External Control' URCap program is playing on the Teach Pendant.")
        tester.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    print("\nCurrent UR5e joint positions captured successfully:")
    for j in tester.ur_joint_names:
        pos_deg = math.degrees(tester.current_ur_positions[j])
        print(f"  - {j:20s} : {pos_deg:+8.2f}° ({tester.current_ur_positions[j]:+.4f} rad)")

    print("\nPlanned Motion Sequence:")
    print("  1. UR5e Arm  : smooth relative rotation of +8.5° on wrist_3_joint, then return to initial pose.")
    print("  2. DG-5F Hand: coordinated 5-finger flexion to mid-stroke, then full release.")
    print("  3. Duration  : 5.0 seconds total (low speed).")
    print("=" * 70)
    print("\n[SAFETY NOTICE]")
    print("  - Keep the Teach Pendant Emergency Stop button within immediate reach.")
    print("  - Ensure no obstacles are near the robotic arm or hand.")

    try:
        input("\nPress [ENTER] to execute the coordinated motion (or Ctrl+C to cancel)... ")
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        tester.destroy_node()
        rclpy.shutdown()
        sys.exit(0)

    tester.execute_motion()
    tester.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
