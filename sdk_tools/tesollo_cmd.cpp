// ==============================================================================
// Author: Kamil BENMADI
// Email: kamil.benmadi@sigma-clermont.fr
// GitHub: https://github.com/1000K-sudo
// LinkedIn: https://www.linkedin.com/in/kamilb-
// ==============================================================================
// tesollo_cmd.cpp — High-speed C++ CLI controller for the Tesollo DG-5F hand
// Communicates directly via Ethernet (Modbus TCP port 502) using DGSDK v1.6.0.
// ==============================================================================

#include <iostream>
#include <thread>
#include <chrono>
#include <cstring>
#include <string>
#include "DGSDK.h"

void OnConnected() {}
void OnDisconnected() {}
void OnData(const ReceivedGripperData data) {}

class TesolloHand {
public:
    bool init(const std::string& ip = "169.254.186.72", int port = 502) {
        GripperSystemSetting setting;
        std::memset(&setting, 0, sizeof(setting));
        setting.port = port;
        setting.baudrate = 115200;
        setting.communicationMode = COMMUNICATION_MODE_ETHERNET;
        setting.controlMode = CONTROL_MODE_OPERATOR;
        setting.readTimeout = 1000;
        setting.slaveID = 1;
        std::strncpy(setting.ip, ip.c_str(), sizeof(setting.ip) - 1);
        std::strncpy(setting.comport, "COM1", sizeof(setting.comport) - 1);

        if (SetGripperSystem(setting) != DG_RESULT_NONE) return false;
        CallbackForOnConnected(OnConnected);
        CallbackForOnDisconnected(OnDisconnected);
        CallbackForOnReceivedGripperData(OnData);

        if (ConnectToGripper() != DG_RESULT_NONE) return false;
        std::this_thread::sleep_for(std::chrono::milliseconds(500));

        GripperSetting gs;
        std::memset(&gs, 0, sizeof(gs));
        gs.model = DG_MODEL_DG_5F_RIGHT;
        gs.movingInpose = 1.0f;
        gs.receivedDataType[0] = 1;
        gs.receivedDataType[1] = 2;
        gs.receivedDataType[2] = 3;
        gs.receivedDataType[3] = 4;
        if (SetGripperOption(gs) != DG_RESULT_NONE) {
            DisconnectToGripper();
            return false;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));

        if (SystemStart() != DG_RESULT_NONE) {
            DisconnectToGripper();
            return false;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        return true;
    }

    void close() {
        SystemStop();
        DisconnectToGripper();
    }

    void zero(int time_ms = 1000) {
        float q[20] = {0};
        SetMotionTimeAllEqual(time_ms);
        MoveJointAll(q);
        std::this_thread::sleep_for(std::chrono::milliseconds(time_ms + 200));
    }

    void flex(float deg = 45.0f, int time_ms = 1000) {
        float q[20] = {
            0, 0, 30.0f, 20.0f,        // Thumb
            0, 0, deg, deg,            // Index
            0, 0, deg, deg,            // Middle
            0, 0, deg, deg,            // Ring
            0, 0, deg, deg             // Pinky
        };
        SetMotionTimeAllEqual(time_ms);
        MoveJointAll(q);
        std::this_thread::sleep_for(std::chrono::milliseconds(time_ms + 200));
    }

    void setFingers(float thumb, float index, float middle, float ring, float pinky, int time_ms = 1000) {
        float q[20] = {
            0, 0, thumb * 0.6f, thumb * 0.4f, // Thumb
            0, 0, index, index,               // Index
            0, 0, middle, middle,             // Middle
            0, 0, ring, ring,                 // Ring
            0, 0, pinky, pinky                // Pinky
        };
        SetMotionTimeAllEqual(time_ms);
        MoveJointAll(q);
        std::this_thread::sleep_for(std::chrono::milliseconds(time_ms + 100));
    }

    void pinch(int time_ms = 1000) {
        float q[20] = {
            0, 0, 35.0f, 25.0f, // Thumb pinch
            0, 0, 45.0f, 35.0f, // Index pinch
            0, 0, 75.0f, 75.0f, // Middle folded
            0, 0, 75.0f, 75.0f, // Ring folded
            0, 0, 75.0f, 75.0f  // Pinky folded
        };
        SetMotionTimeAllEqual(time_ms);
        MoveJointAll(q);
        std::this_thread::sleep_for(std::chrono::milliseconds(time_ms + 100));
    }

    void point(int time_ms = 1000) {
        float q[20] = {
            0, 0, 30.0f, 20.0f, // Thumb tucked
            0, 0, 0.0f,  0.0f,  // Index extended
            0, 0, 75.0f, 75.0f, // Middle folded
            0, 0, 75.0f, 75.0f, // Ring folded
            0, 0, 75.0f, 75.0f  // Pinky folded
        };
        SetMotionTimeAllEqual(time_ms);
        MoveJointAll(q);
        std::this_thread::sleep_for(std::chrono::milliseconds(time_ms + 100));
    }

    void grasp() {
        StartGraspMotion(1);
        std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    }

    void release() {
        StartGraspMotion(0);
        std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    }
};

int main(int argc, char* argv[]) {
    std::string cmd = (argc > 1) ? argv[1] : "help";

    if (cmd == "help" || cmd == "-h" || cmd == "--help") {
        std::cout << "Usage: ./tesollo_cmd [zero|flex <deg>|set_fingers <T> <I> <M> <R> <P>|grasp|release|pinch|point]" << std::endl;
        return 0;
    }

    TesolloHand hand;
    std::cout << "[Tesollo] Connecting to hand at 169.254.186.72:502..." << std::endl;
    if (!hand.init()) {
        std::cerr << "[ERROR] Failed to connect to Tesollo DG-5F hand!" << std::endl;
        return 1;
    }
    std::cout << "[Tesollo] Connected successfully." << std::endl;

    if (cmd == "zero") {
        std::cout << "[Tesollo] Moving to zero (open) posture..." << std::endl;
        hand.zero();
    } else if (cmd == "flex") {
        float deg = (argc > 2) ? std::stof(argv[2]) : 45.0f;
        std::cout << "[Tesollo] Flexing fingers to " << deg << " deg..." << std::endl;
        hand.flex(deg);
    } else if (cmd == "set_fingers" && argc >= 7) {
        float t = std::stof(argv[2]);
        float i = std::stof(argv[3]);
        float m = std::stof(argv[4]);
        float r = std::stof(argv[5]);
        float p = std::stof(argv[6]);
        int tm = (argc > 7) ? std::stoi(argv[7]) : 1000;
        std::cout << "[Tesollo] Setting fingers: T=" << t << " I=" << i << " M=" << m << " R=" << r << " P=" << p << std::endl;
        hand.setFingers(t, i, m, r, p, tm);
    } else if (cmd == "pinch") {
        std::cout << "[Tesollo] Executing 2-finger pinch..." << std::endl;
        hand.pinch();
    } else if (cmd == "point") {
        std::cout << "[Tesollo] Executing index point..." << std::endl;
        hand.point();
    } else if (cmd == "grasp") {
        std::cout << "[Tesollo] Closing hand (Grasp)..." << std::endl;
        hand.grasp();
    } else if (cmd == "release" || cmd == "open") {
        std::cout << "[Tesollo] Opening hand (Release)..." << std::endl;
        hand.release();
    } else {
        std::cerr << "Unknown command or missing arguments: " << cmd << std::endl;
    }

    hand.close();
    std::cout << "[Tesollo] Disconnected cleanly." << std::endl;
    return 0;
}
