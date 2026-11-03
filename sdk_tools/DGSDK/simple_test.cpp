// ==============================================================================
// Author: Kamil BENMADI
// Email: kamil.benmadi@sigma-clermont.fr
// GitHub: https://github.com/1000K-sudo
// LinkedIn: https://www.linkedin.com/in/kamilb-
// ==============================================================================
#include <iostream>
#include <thread>
#include <chrono>
#include <cstring>
#include <DGSDK.h>

// Callbacks
void OnConnected() {
    std::cout << "\n[Callback] Successfully connected to Delto Gripper!" << std::endl;
}

void OnDisconnected() {
    std::cout << "\n[Callback] Disconnected from Delto Gripper!" << std::endl;
}

void OnReceivedGripperData(const ReceivedGripperData gripperData) {
    std::cout << "\r[Callback] Target Arrived: " << gripperData.targetArrived 
              << " | Moving: " << gripperData.moving 
              << " | Motor 1 Temp: " << (int)gripperData.temperature[0] << " C" 
              << " | Joint[0]: " << gripperData.joint[0]
              << "   " << std::flush;
}

int main(int argc, char* argv[]) {
    std::string ip_addr = "169.254.186.72";
    if (argc > 1) {
        ip_addr = argv[1];
    }
    
    std::cout << "=== Tesollo DGSDK Linux Connection Test ===" << std::endl;
    std::cout << "Target IP address: " << ip_addr << " (port 502)" << std::endl;
    
    // Gripper system configuration
    GripperSystemSetting setting;
    std::memset(&setting, 0, sizeof(setting));
    
    setting.port = 502;
    setting.baudrate = 115200;
    setting.communicationMode = COMMUNICATION_MODE_ETHERNET;
    setting.controlMode = CONTROL_MODE_OPERATOR;
    setting.readTimeout = 1000;
    setting.slaveID = 1;
    
    std::strncpy(setting.ip, ip_addr.c_str(), MAX_GRIPPER_IP_ADDRESS_SIZE - 1);
    std::strncpy(setting.comport, "COM1", MAX_COMPORT_NAME_SIZE - 1);
    
    // Register callbacks
    CallbackForOnConnected(OnConnected);
    CallbackForOnDisconnected(OnDisconnected);
    CallbackForOnReceivedGripperData(OnReceivedGripperData);
    
    // Set gripper system
    std::cout << "Setting gripper configuration..." << std::endl;
    DG_RESULT res = SetGripperSystem(setting);
    if (res != DG_RESULT_NONE) {
        std::cerr << "Error setting gripper system parameters. Code: " << (int)res << std::endl;
        return 1;
    }
    
    // Connect
    std::cout << "Connecting to gripper..." << std::endl;
    res = ConnectToGripper();
    if (res != DG_RESULT_NONE) {
        std::cerr << "Error connecting to gripper. Code: " << (int)res << std::endl;
        return 1;
    }
    
    // Start system
    std::cout << "Starting background communication system..." << std::endl;
    res = SystemStart();
    if (res != DG_RESULT_NONE) {
        std::cerr << "Error starting communication system. Code: " << (int)res << std::endl;
        DisconnectToGripper();
        return 1;
    }
    
    std::cout << "Connection active. Monitoring gripper feedback for 10 seconds..." << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(10));
    
    // Stop system
    std::cout << "\nStopping background system..." << std::endl;
    SystemStop();
    
    // Disconnect
    std::cout << "Disconnecting from gripper..." << std::endl;
    DisconnectToGripper();
    
    std::cout << "Test completed successfully!" << std::endl;
    return 0;
}
