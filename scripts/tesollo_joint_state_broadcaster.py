#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
tesollo_joint_state_broadcaster.py
==================================
Continuously broadcasts the 20 real joint angles of the Tesollo DG-5F hand
on the ROS 2 `/joint_states` topic (in radians) to update the TF tree in RViz2.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import ctypes
import math
import time
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
LIB_DGSDK_PATH = (
    "/usr/local/lib/libDGSDK.so"
    if os.path.isfile("/usr/local/lib/libDGSDK.so")
    else os.path.join(WORKSPACE_DIR, "sdk_tools", "DGSDK", "libDGSDK.so")
)

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

class TesolloJointStateBroadcaster(Node):
    def __init__(self):
        super().__init__('tesollo_joint_state_broadcaster')
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        
        self.joint_names = [
            "rj_dg_1_1", "rj_dg_1_2", "rj_dg_1_3", "rj_dg_1_4",  # Pouce
            "rj_dg_2_1", "rj_dg_2_2", "rj_dg_2_3", "rj_dg_2_4",  # Index
            "rj_dg_3_1", "rj_dg_3_2", "rj_dg_3_3", "rj_dg_3_4",  # Majeur
            "rj_dg_4_1", "rj_dg_4_2", "rj_dg_4_3", "rj_dg_4_4",  # Annulaire
            "rj_dg_5_1", "rj_dg_5_2", "rj_dg_5_3", "rj_dg_5_4",  # Auriculaire
        ]

        if not os.path.isfile(LIB_DGSDK_PATH):
            self.get_logger().error(f"Bibliothèque {LIB_DGSDK_PATH} introuvable.")
            sys.exit(1)

        self.lib = ctypes.CDLL(LIB_DGSDK_PATH)
        self._init_sdk()

    def _init_sdk(self):
        self.lib.SetGripperSystem.argtypes = [GripperSystemSetting]
        self.lib.SetGripperSystem.restype = ctypes.c_int
        self.lib.SetGripperOption.argtypes = [GripperSetting]
        self.lib.SetGripperOption.restype = ctypes.c_int
        self.lib.ConnectToGripper.restype = ctypes.c_int
        self.lib.SystemStart.restype = ctypes.c_int
        self.lib.SystemStop.restype = ctypes.c_int
        self.lib.DisconnectToGripper.restype = ctypes.c_int

        self.ON_DATA_FUNC = ctypes.CFUNCTYPE(None, ReceivedGripperData)
        self.lib.CallbackForOnReceivedGripperData.argtypes = [self.ON_DATA_FUNC]
        self._cb_holder = self.ON_DATA_FUNC(self._on_data_cb)
        self.lib.CallbackForOnReceivedGripperData(self._cb_holder)

        sys_set = GripperSystemSetting()
        sys_set.port = 502
        sys_set.baudrate = 115200
        sys_set.communicationMode = 1  # ETHERNET
        sys_set.controlMode = 0        # OPERATOR
        sys_set.readTimeout = 1000
        sys_set.slaveID = 1
        sys_set.ip = b"169.254.186.72"
        sys_set.comport = b"COM1"

        if self.lib.SetGripperSystem(sys_set) != 0:
            self.get_logger().error("Échec SetGripperSystem")
            return

        if self.lib.ConnectToGripper() != 0:
            self.get_logger().error("Impossible de se connecter à la main Tesollo (169.254.186.72:502)")
            return

        time.sleep(0.4)
        gs = GripperSetting()
        gs.model = 4  # DG_5F_RIGHT
        gs.movingInpose = 1.0
        gs.receivedDataType[0] = 1
        gs.receivedDataType[1] = 2
        gs.receivedDataType[2] = 3
        gs.receivedDataType[3] = 4
        self.lib.SetGripperOption(gs)
        time.sleep(0.5)

        if self.lib.SystemStart() != 0:
            self.get_logger().error("Échec SystemStart")
            return

        self.get_logger().info("✅ Connecté à la main Tesollo DG-5F. Diffusion temps réel sur /joint_states active.")

    def _on_data_cb(self, data: ReceivedGripperData):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        # Conversion impérative Degrés -> Radians
        msg.position = [math.radians(float(data.joint[i])) for i in range(20)]
        self.pub.publish(msg)

    def destroy_node(self):
        try:
            self.lib.SystemStop()
            self.lib.DisconnectToGripper()
        except Exception:
            pass
        super().destroy_node()

def main():
    rclpy.init()
    node = TesolloJointStateBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
