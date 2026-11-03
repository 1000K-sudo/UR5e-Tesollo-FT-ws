#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
dg5f_rsp.launch.py
==================
Launches the Robot State Publisher for the Tesollo DG-5F right hand and publishes
the static transform linking the UR5e tool flange (tool0) to the hand base (right_base_link).
"""

import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('dg_description')
    xacro_file = os.path.join(pkg_share, 'urdf', 'dg5f_right.xacro')
    doc = xacro.process_file(xacro_file)
    robot_desc = doc.toxml()

    return LaunchDescription([
        # 1. Kinematic description and TF tree publication for the Tesollo DG-5F hand
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace='dg5f_right',
            output='screen',
            parameters=[{'robot_description': robot_desc}],
            remappings=[('/dg5f_right/joint_states', '/joint_states')]
        ),
        # 2. Static spatial transform: UR5e flange (tool0) -> Tesollo base (right_base_link)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tool0_to_tesollo_tf',
            output='screen',
            arguments=[
                '--x', '0.0',
                '--y', '0.0',
                '--z', '0.070',
                '--roll', '0.0',
                '--pitch', '0.0',
                '--yaw', '1.5708',
                '--frame-id', 'tool0',
                '--child-frame-id', 'right_base_link'
            ]
        )
    ])
