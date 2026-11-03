#include <iostream>
#include <list>
#include <thread>
#include "DGSDK.h"
#include <format>
#include <conio.h>
#include <stdlib.h>
#include <functional>
#include <vector>
#include <windows.h>
#include <string>

#pragma comment(lib, "DGSDK.lib")

void EnableVTMode() {
	HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
	if (hOut == INVALID_HANDLE_VALUE) return;

	DWORD dwMode = 0;
	if (!GetConsoleMode(hOut, &dwMode)) return;

	dwMode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
	SetConsoleMode(hOut, dwMode);
}

using namespace std;

void Display();

ReceivedGripperData gripperData;
ReceivedFingertipSensorData sensorData;
ReceivedGPIOData gpioData;

DiagnosisSystem diag;

float targetTCP[30];
float pos[12];
int countPeriod = 0;
bool isConnected = false;
bool clearConsole = false;

void RecvCommand();

static void OnConnected()
{
	std::cout << "Connected gripper server" << std::endl;
	isConnected = true;
}
static void OnDisconnected()
{
	std::cout << "Disconnected gripper server" << std::endl;
	isConnected = false;
}
static void RecvGripperData(const ReceivedGripperData data)
{
	gripperData = data;
}
static void OnCountPeriod(const int period)
{
	countPeriod = period;
}
static void OnDiagnosisData(const DiagnosisSystem diagnose)
{
	diag = diagnose;
}
static void RecvSensorData(const ReceivedFingertipSensorData recvSensorData)
{
	sensorData = recvSensorData;
}
static void RecvGPIOData(const ReceivedGPIOData recvGPIOData)
{
	gpioData = recvGPIOData;
}

void InitializedCallback()
{
	CallbackForOnConnected(*OnConnected);
	CallbackForOnDisconnected(*OnDisconnected);
	CallbackForOnReceivedGripperData(*RecvGripperData);
	CallbackForOnCommunicationPeriod(*OnCountPeriod);
	CallbackForOnDiagnosisSystem(*OnDiagnosisData);
	CallbackForOnReceivedFingertipSensorData(*RecvSensorData);
	CallbackForOnReceivedGPIOData(*RecvGPIOData);
}

void setConsoleSize(int width, int height) {
	HWND console = GetConsoleWindow();
	RECT r;
	GetWindowRect(console, &r);
	MoveWindow(console, r.left, r.top, width, height, TRUE);
}

int main()
{
	EnableVTMode();
	setConsoleSize(900, 400);  // 너비, 높이 (단위: 픽셀)

	//GripperSystemSetting setting;
	//
	//std::string ip = "169.254.186.73";
	//std::string input = "";

	//std::cout << endl << "\n1. Set IP : 169.254.186.72 (default)\n\n   Enter : ";
	//std::getline(cin, input);

	//memcpy(setting.ip, input.c_str(), sizeof(setting.ip));
	//std::cout << "\033[H\033[J\033[3J" << std::flush;

	//std::cout << endl << "\n2. Set PORT : 502 (default)\n\n   Enter : ";
	//std::getline(cin, input);

	//setting.port = std::stoi(input);
	//std::cout << "\033[H\033[J\033[3J" << std::flush;

	//std::cout << endl << "\n2. Set COM : COM3 (default)\n\n   Enter : ";
	//std::getline(cin, input);

	//memcpy(setting.comport, input.c_str(), sizeof(setting.comport));
	//std::cout << "\033[H\033[J\033[3J" << std::flush;

	//std::cout << endl << "\n3. Set communicate Mode : 0 / 1 ( COMMUNICATION_MODE_ETHERNET / COMMUNICATION_MODE_RS485 )\n\n   Enter : ";
	//std::getline(cin, input);

	//setting.communicationMode = std::stoi(input);
	//std::cout << "\033[H\033[J\033[3J" << std::flush;

	//std::cout << endl << "\n4. Set control Mode : 0 / 1 ( CONTROL_MODE_OPERATOR / CONTROL_MODE_DEVELOPER )\n\n   Enter : ";
	//std::getline(cin, input);

	//setting.controlMode = std::stoi(input);
	//std::cout << "\033[H\033[J\033[3J" << std::flush;

	//setting.baudrate = 115200;
	//setting.readTimeout = 1000;
	//setting.slaveID = 1;

	////memcpy(setting.ip, ip.c_str(), MAX_GRIPPER_IP_ADRRESS_SIZE);
	////memcpy(setting.comport, com.c_str(), MAX_COMPORT_NAME_SIZE);

	//SetGripperSystem(setting);
	//InitializedCallback();
	//ConnectToGripper();

	//while (!isConnected)
	//{
	//	std::this_thread::sleep_for(std::chrono::milliseconds(1));
	//}

	//GripperSetting gs;

	//std::cout << endl << "\n Set Gripper Model : 1 / 2 / 3 / 4 ( DG_MODEL_DG_3F_M / DG_MODEL_DG_4F_M / DG_MODEL_DG_5F_LEFT / DG_MODEL_DG_5F_RIGHT )\n\n   Enter : ";
	//std::getline(cin, input);

	//int m = std::stoi(input);
	//std::cout << "\033[H\033[J\033[3J" << std::flush;

	//switch (m)
	//{
	//case 1:
	//{
	//	gs.model = DG_MODEL_DG_3F_M;
	//	break;
	//}
	//case 2:
	//{
	//	gs.model = DG_MODEL_DG_4F_M;
	//	break;
	//}
	//case 3:
	//{
	//	gs.model = DG_MODEL_DG_5F_LEFT;
	//	break;
	//}
	//case 4:
	//{
	//	gs.model = DG_MODEL_DG_5F_RIGHT;
	//	break;
	//}
	//default:
	//{
	//	break;
	//}
	//};

	//float jointInpose[MAX_JOINT_COUNT] = { 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
	//float jointOffset[MAX_JOINT_COUNT] = { 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };

	//int type[MAX_RECEIVED_DATA_TYPE_COUNT] = { 1,2,3,4,5,6 };

	//gs.movingInpose = 1;

	//memcpy(gs.jointInpose, jointInpose, sizeof(jointInpose));
	//memcpy(gs.jointOffset, jointOffset, sizeof(jointOffset));
	//memcpy(gs.receivedDataType, type, sizeof(type));

	//SetGripperOption(gs);


	//float P[20] = { 1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1 };
	//float D[20] = { 5,5,5,5, 5,5,5,5, 5,5,5,5, 5,5,5,5, 5,5,5,5 };
	//float I[20] = { 1,1,1,1, 1,1,1,1, 1,1,1,1 ,1,1,1,1, 1,1,1,1 };
	//float ILimit[20] = { 1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1 };

	//for (int i = 0; i < 20; i++)
	//{
	//	P[i] = 1;
	//	D[i] = 3;
	//}

	//SetJointGainPAll(P);
	//SetJointGainDAll(D);
	//SetJointGainIAll(I, ILimit);

	//std::this_thread::sleep_for(std::chrono::milliseconds(1000));
	//SystemStart();

	//SetMotionTimeAllEqual(500);

	setConsoleSize(800, 1000);  // 너비, 높이 (단위: 픽셀)

	//string joint = "";

	thread thd(RecvCommand);
	thd.detach();

	while (true)
	{
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
		Display();
	}
	thd.join();
	return 0;
}

typedef struct KeyCommand
{
	char mainCommand;
	char jointCommand;
	char TCPCommand;
	char graspCommand;
	char manipulationCommand;
	char gainCommand;
	char motionSetCommand;
	char currentCommand;
	char recipeCommand;
	char systemCommand;

	std::string cmdString = "";
}KeyCommand;

KeyCommand key;
int modeCommand = 0;

void JointCommand(string* str);
void TCPCommand(string* str);
void GraspCommand(string* str);
void ManipulationCommand(string* str);
void GainCommand(string* str);
void MotionSetCommand(string* str);
void CurrentCommand(string* str);
void RecipeCommand(string* str);
void SystemCommand(string* str);

void Display()
{
	int i = 0;

	string str = " ==== Command ====\n";
	string mStr = "";

	if (key.mainCommand == 'j')
	{
		key.cmdString = "";
		modeCommand = 1;
		str += " Joint \033[40G Check \"JointCommand()\"\n";
		JointCommand(&str);
	}
	else if (key.mainCommand == 'm')
	{
		key.cmdString = "";
		modeCommand = 6;
		str += " Motion Set \033[40G Check \"MotionSetCommand()\"\n";
		MotionSetCommand(&str);
	}
	else if (key.mainCommand == 'g')
	{
		key.cmdString = "";
		modeCommand = 3;
		str += " Grasp Setting\033[40G Check \"GraspCommand()\"\n";
		GraspCommand(&str);
	}
	else if (key.mainCommand == 's')
	{
		key.cmdString = "";
		modeCommand = 5;
		str += " Setting \033[40G Check \"GainCommand()\"\n";
		GainCommand(&str);
	}
	else if (key.mainCommand == 'l')
	{
		key.cmdString = "";
		modeCommand = 2;
		str += " TCP \033[40G Check \"TCPCommand()\"\n";
		TCPCommand(&str);
	}
	else if (key.mainCommand == 'h')
	{
		key.cmdString = "";
		modeCommand = 4;
		str += " Manipulation \033[40G Check \"ManipulationCommand()\"\n";
		ManipulationCommand(&str);
	}
	else if (key.mainCommand == 'q')
	{
		key.cmdString = "";
		modeCommand = 7;
		str += " Current \033[40G Check \"CurrentCommand()\"\n";
		CurrentCommand(&str);
	}
	else if (key.mainCommand == 'e')
	{
		key.cmdString = "";
		modeCommand = 8;
		str += " Recipe \033[40G Check \"RecipeCommrand()\"\n";
		RecipeCommand(&str);
	}
	else if (key.mainCommand == 'o')
	{
		key.cmdString = "";
		modeCommand = 9;
		str += " System \033[40G Check \"SystemCommand()\"\n";
		SystemCommand(&str);
	}
	else if (key.mainCommand == 't')
	{
		key.cmdString = "\n Manual Teach Mode \n";
		ManualTeachMode(1);
		key.mainCommand = NULL;
	}
	else if (key.mainCommand == 'c')
	{
		key.cmdString = "\n Control Mode \n";
		ManualTeachMode(0);
		key.mainCommand = NULL;
	}
	else if (key.mainCommand == 'd')
	{
		str += "\n Diagnosis \n";
		SystemDiagnosis();
		key.mainCommand = NULL;
	}
	else
	{
		str += "\033[K Main                       \n";
		str += format("[j] : Joint Motion\n[m] : Motion Set\n[g] : Grasp Motion\n[s] : Gain Set\n[l] : TCP Motion\n[q] : Current Motion\n[h] : InHandManipulation\n[e] : Recipes\n[o] : System\n[t] : Manual Teach Mode\n[c] : Control Mode\n[d] : Diagnosis\n");
		str += key.cmdString;
	}

	mStr += " ==== Data Display ====				\n\n";
	mStr += format("Communication Period : {0} Hz\t\n\n", countPeriod);

	mStr += format(" Joint /  j1,  j2,   j3,   j4							\n\n");
	mStr += format("\033[KThumb  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.joint[0], gripperData.joint[1], gripperData.joint[2], gripperData.joint[3]);
	mStr += format("\033[KIndex  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.joint[0 + 4], gripperData.joint[1 + 4], gripperData.joint[2 + 4], gripperData.joint[3 + 4]);
	mStr += format("\033[KMiddle : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.joint[0 + 8], gripperData.joint[1 + 8], gripperData.joint[2 + 8], gripperData.joint[3 + 8]);
	mStr += format("\033[KRinger : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.joint[0 + 12], gripperData.joint[1 + 12], gripperData.joint[2 + 12], gripperData.joint[3 + 12]);
	mStr += format("\033[KPinky  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n\n", gripperData.joint[0 + 16], gripperData.joint[1 + 16], gripperData.joint[2 + 16], gripperData.joint[3 + 16]);

	mStr += format("\033[KThumb  : {0}, {1}, {2}, {3}								\n", gripperData.current[0], gripperData.current[1], gripperData.current[2], gripperData.current[3]);
	mStr += format("\033[KIndex  : {0}, {1}, {2}, {3}								\n", gripperData.current[0 + 4], gripperData.current[1 + 4], gripperData.current[2 + 4], gripperData.current[3 + 4]);
	mStr += format("\033[KMiddle : {0}, {1}, {2}, {3}								\n", gripperData.current[0 + 8], gripperData.current[1 + 8], gripperData.current[2 + 8], gripperData.current[3 + 8]);
	mStr += format("\033[KRinger : {0}, {1}, {2}, {3}								\n", gripperData.current[0 + 12], gripperData.current[1 + 12], gripperData.current[2 + 12], gripperData.current[3 + 12]);
	mStr += format("\033[KPinky  : {0}, {1}, {2}, {3}								\n\n", gripperData.current[0 + 16], gripperData.current[1 + 16], gripperData.current[2 + 16], gripperData.current[3 + 16]);

	mStr += format("\033[KThumb  : {0}, {1}, {2}, {3}								\n", gripperData.velocity[0], gripperData.velocity[1], gripperData.velocity[2], gripperData.velocity[3]);
	mStr += format("\033[KIndex  : {0}, {1}, {2}, {3}								\n", gripperData.velocity[0 + 4], gripperData.velocity[1 + 4], gripperData.velocity[2 + 4], gripperData.velocity[3 + 4]);
	mStr += format("\033[KMiddle : {0}, {1}, {2}, {3}								\n", gripperData.velocity[0 + 8], gripperData.velocity[1 + 8], gripperData.velocity[2 + 8], gripperData.velocity[3 + 8]);
	mStr += format("\033[KRinger : {0}, {1}, {2}, {3}								\n", gripperData.velocity[0 + 12], gripperData.velocity[1 + 12], gripperData.velocity[2 + 12], gripperData.velocity[3 + 12]);
	mStr += format("\033[KPinky  : {0}, {1}, {2}, {3}								\n\n", gripperData.velocity[0 + 16], gripperData.velocity[1 + 16], gripperData.velocity[2 + 16], gripperData.velocity[3 + 16]);

	mStr += format("\033[KThumb  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.temperature[0], gripperData.temperature[1], gripperData.temperature[2], gripperData.temperature[3]);
	mStr += format("\033[KIndex  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.temperature[0 + 4], gripperData.temperature[1 + 4], gripperData.temperature[2 + 4], gripperData.temperature[3 + 4]);
	mStr += format("\033[KMiddle : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.temperature[0 + 8], gripperData.temperature[1 + 8], gripperData.temperature[2 + 8], gripperData.temperature[3 + 8]);
	mStr += format("\033[KRinger : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n", gripperData.temperature[0 + 12], gripperData.temperature[1 + 12], gripperData.temperature[2 + 12], gripperData.temperature[3 + 12]);
	mStr += format("\033[KPinky  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}				\n\n", gripperData.temperature[0 + 16], gripperData.temperature[1 + 16], gripperData.temperature[2 + 16], gripperData.temperature[3 + 16]);

	mStr += format(" TCP  /   x,    y,    z				\n\n");
	mStr += format("\033[KThumb  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.2f}, {4:.2f}, {5:.2f}				\n", gripperData.TCP[0] * 1000, gripperData.TCP[1] * 1000, gripperData.TCP[2] * 1000, gripperData.TCP[3], gripperData.TCP[4], gripperData.TCP[5]);
	mStr += format("\033[KIndex  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.2f}, {4:.2f}, {5:.2f}				\n", gripperData.TCP[0 + 6] * 1000, gripperData.TCP[1 + 6] * 1000, gripperData.TCP[2 + 6] * 1000, gripperData.TCP[3 + 6], gripperData.TCP[4 + 6], gripperData.TCP[5 + 6]);
	mStr += format("\033[KMiddle : {0:.1f}, {1:.1f}, {2:.1f}, {3:.2f}, {4:.2f}, {5:.2f}				\n", gripperData.TCP[0 + 12] * 1000, gripperData.TCP[1 + 12] * 1000, gripperData.TCP[2 + 12] * 1000, gripperData.TCP[3 + 12], gripperData.TCP[4 + 12], gripperData.TCP[5 + 12]);
	mStr += format("\033[KRinger : {0:.1f}, {1:.1f}, {2:.1f}, {3:.2f}, {4:.2f}, {5:.2f}				\n", gripperData.TCP[0 + 18] * 1000, gripperData.TCP[1 + 18] * 1000, gripperData.TCP[2 + 18] * 1000, gripperData.TCP[3 + 18], gripperData.TCP[4 + 18], gripperData.TCP[5 + 18]);
	mStr += format("\033[KPinky  : {0:.1f}, {1:.1f}, {2:.1f}, {3:.2f}, {4:.2f}, {5:.2f}               \n", gripperData.TCP[0 + 24] * 1000, gripperData.TCP[1 + 24] * 1000, gripperData.TCP[2 + 24] * 1000, gripperData.TCP[3 + 24], gripperData.TCP[4 + 24], gripperData.TCP[5 + 24]);

	std::cout << "\033[H" << std::flush;
	std::cout << str << std::flush;
	std::cout << "\033[17;0f \n\n" << std::flush;
	std::cout << mStr << std::flush;

	std::this_thread::sleep_for(std::chrono::milliseconds(50));
	std::cout << "\033[?25h" << std::flush;

	if (clearConsole)
	{
		clearConsole = false;
		std::cout << "\033[H\033[J\033[3J\033[2K\033[?25h" << std::flush;
	}
}

void RecvCommand()
{
	while (1)
	{
		char input = _getch();

		switch (modeCommand)
		{
		case 0:					// Main
		{
			key.jointCommand = NULL;
			key.TCPCommand = NULL;
			key.graspCommand = NULL;
			key.manipulationCommand = NULL;
			key.gainCommand = NULL;
			key.motionSetCommand = NULL;
			key.currentCommand = NULL;
			key.recipeCommand = NULL;
			key.systemCommand = NULL;

			key.mainCommand = input;
			break;
		}
		case 1:					// Joint
		{
			key.jointCommand = input;
			break;
		}
		case 2:					// TCP
		{
			key.TCPCommand = input;
			break;
		}
		case 3:					// Grasp
		{
			key.graspCommand = input;
			break;
		}
		case 4:					// Manipulation
		{
			key.manipulationCommand = input;
			break;
		}
		case 5:					// Gain
		{
			key.gainCommand = input;
			break;
		}
		case 6:					// MotionSet
		{
			key.motionSetCommand = input;
			break;
		}
		case 7:					// current
		{
			key.currentCommand = input;
			break;
		}
		case 8:					// recipe
		{
			key.recipeCommand = input;
			break;
		}
		case 9:					// system
		{
			key.systemCommand = input;
			break;
		}
		}
		clearConsole = true;
	}
}

void SystemCommand(string* str)
{
	if (key.systemCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.systemCommand == '1')
	{
		key.cmdString = "\n System Setting \n";

		GripperSystemSetting setting;
		std::string ip = "169.254.186.72";
		std::string com = "COM5";

		setting.port = 502;
		setting.baudrate = 115200;
		setting.communicationMode = COMMUNICATION_MODE_ETHERNET;
		//setting.communicationMode = COMMUNICATION_MODE_RS485;
		//setting.controlMode = CONTROL_MODE_DEVELOPER;
		setting.controlMode = CONTROL_MODE_OPERATOR;
		setting.readTimeout = 1000;
		setting.slaveID = 1;

		memcpy(setting.ip, ip.c_str(), MAX_GRIPPER_IP_ADDRESS_SIZE);
		memcpy(setting.comport, com.c_str(), MAX_COMPORT_NAME_SIZE);

		SetGripperSystem(setting);
		InitializedCallback();
		ConnectToGripper();
	}
	else if (key.systemCommand == '2')
	{
		key.cmdString = "\n Gripper Option Setting\n";

		GripperSetting gs;
		float jointInpose[MAX_JOINT_COUNT] = { 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
		float jointOffset[MAX_JOINT_COUNT] = { 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };

		int type[MAX_RECEIVED_DATA_TYPE_COUNT] = { 1,2,3,4,0,0 };

		gs.model = DG_MODEL_DG_4F_M;
		gs.movingInpose = 1;
		memcpy(gs.jointInpose, jointInpose, sizeof(jointInpose));
		memcpy(gs.jointOffset, jointOffset, sizeof(jointOffset));
		memcpy(gs.receivedDataType, type, sizeof(type));

		SetGripperOption(gs);
	}
	else if (key.systemCommand == '3')
	{
		key.cmdString = "\n System Start\n";
		int result = SystemStart();
		int a = 0;
	}
	else if (key.systemCommand == '4')
	{
		key.cmdString = "\n System Stop\n";
		SystemStop();
	}
	else if (key.systemCommand == '5')
	{
		key.cmdString = "\n Set IP, Port\n";

		int ip[4] = { 169,254,186,72 };
		int port = 502;

		SetIp(ip, port);
	}
	else if (key.systemCommand == '6')
	{
		key.cmdString = "\n Set GPIO\n";

		int gpio = 1;
		int outputNumber = 1;

		SetGPIOOuput(gpio, outputNumber);
	}
	else if (key.systemCommand == '7')
	{
		key.cmdString = "\n Set GPIO All\n";

		int gpio[3] = { 1,0,1 };

		SetGPIOOuputAll(gpio);
	}
	else if (key.systemCommand == '8')
	{
		key.cmdString = "\n Backup Recipes\n";

		//std::string directory = "C:/Users/Tesollo/Desktop/{FolderName}";
		std::string directory = "C:/Users/PIH/Desktop/DGManager/Backup";
		char dir[1024];

		memcpy(dir, directory.c_str(), 1024);

		BackupRecipeData(dir);
	}
	else if (key.systemCommand == '9')
	{
		key.cmdString = "\n Restore Recipes\n";

		std::string directory = "C:/Users/Tesollo/Desktop/{FolderName}";
		char dir[1024];

		memcpy(dir, directory.c_str(), 1024);

		RestoreRecipeData(dir);
	}
	else if (key.systemCommand == 'l')
	{
		key.cmdString = "\n Set Lowpassfilter\n";
		bool isUsed = true;
		float alpha = 0.15;
		SetLowPassFilterAlpha(isUsed, alpha);
	}
	else if (key.systemCommand == 'a')
	{
		key.cmdString = "\n Get Received Gripper Data\n";
		ReceivedGripperData recvGripperData;
		GetReceivedGripperData(&recvGripperData);
	}
	else if (key.systemCommand == 's')
	{
		key.cmdString = "\n Get Communication Period\n";
		int CommunicationPeriod;
		GetCommunicationPeriod(&CommunicationPeriod);
	}
	else if (key.systemCommand == 'd')
	{
		key.cmdString = "\n Get Finger tip Sensor Data\n";
		ReceivedFingertipSensorData recvFingertipData;
		GetReceivedFingertipSensorData(&recvFingertipData);
	}
	else if (key.systemCommand == 'f')
	{
		key.cmdString = "\n Get GPIO Data\n";
		ReceivedGPIOData recvGPIOData;
		GetReceivedGPIOData(&recvGPIOData);
	}
	else
	{
		str->append(format("[c] : return\n[1] : System Setting\n[2] : Gripper Option Setting\n[3] : System Start\n[4] : System Stop\n[5] : Set IP, Port\n[6] : Set GPIO\n[7] : Set GPIO All\n[8] : Backup Recipes\n[9] : Restore Recipes\n[l] : Set Lowpassfilter\n"
			"[a] : Get Received Gripper Data\n[s] : Get Communication Period\n[d] : Get Finger tip Sensor Data\n[f] : Get GPIO Data\n"));
	}
	key.systemCommand = NULL;
}

void JointCommand(string* str)
{
	int idx = 0;

	if (key.jointCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.jointCommand == '1')
	{
		key.cmdString = "\n MoveJoint\n";

		float targetJoint = 0;
		for (int i = 0; i < MAX_JOINT_COUNT; i++) MoveJoint(targetJoint, i);
	}
	else if (key.jointCommand == '2')
	{
		key.cmdString = "\n MoveJointFinger\n";

		float targetJoint[4] = { 0,0,0,0 };
		for (int i = 0; i < MAX_FINGER_COUNT; i++) MoveJointFinger(targetJoint, i);
	}
	else if (key.jointCommand == '3')
	{
		key.cmdString = "\n MoveJointAll\n";

		float targetJoint[20] = { 0,0,20,10,    -2,73.2,89.5,85.7,    -1.8,83.6,80.4,76.6,    -0.5,77,86.8,91.5,    2.2,-0.1,91.2,89.9 };
		MoveJointAll(targetJoint);
	}
	else if (key.jointCommand == '4')
	{
		key.cmdString = "\n MoveServoJoint\n";

		float targetJoint[20] = { 0,0,20,10,    -2,73.2,89.5,85.7,    -1.8,83.6,80.4,76.6,    -0.5,77,86.8,91.5,    2.2,-0.1,91.2,89.9 };
		MoveServoJoint(targetJoint);

		for (int i = 0; i < MAX_JOINT_COUNT; i++) targetJoint[i] += 1;
		MoveServoJoint(targetJoint);

		for (int i = 0; i < MAX_JOINT_COUNT; i++) targetJoint[i] += 1;
		MoveServoJoint(targetJoint);

		for (int i = 0; i < MAX_JOINT_COUNT; i++) targetJoint[i] += 1;
		MoveServoJoint(targetJoint);
	}
	else if (key.jointCommand == '5')
	{
		key.cmdString = "\n MoveJointBase\n";

		float targetJoint[2] = { 0,0 };
		MoveJointBase(targetJoint);
	}
	else if (key.jointCommand == 'x')
	{
		key.cmdString = "\n Zero Pose\n";

		float targetJoint[20] = { 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
		MoveJointAll(targetJoint);
	}
	else
	{
		str->append(format("[c] : return\n[1] : Move Joint\n[2] : Move Joint Finger\n[3] : Move Joint All\n[4] : Move Servo Joint \n[5] : Move Joint Base ( DG-4F-M )\n[x] : Zero pose\n"));
	}
	key.jointCommand = NULL;
}

void CurrentCommand(string* str)
{
	int idx = 0;

	if (key.currentCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.currentCommand == '1')
	{
		key.cmdString = "\n Set CurrentControlMode On\n";

		SetCurrentControlMode(1);
	}
	else if (key.currentCommand == '2')
	{
		key.cmdString = "\n Set CurrentControlMode Off\n";

		SetCurrentControlMode(0);
	}
	else if (key.currentCommand == '3')
	{
		key.cmdString = "\n Set Target Current(mA)\n";

		int targetCurrent = 50;
		for (int i = 0; i < MAX_JOINT_COUNT; i++)
		{
			SetTargetCurrentJoint(targetCurrent, i);
		}
	}
	else if (key.currentCommand == '4')
	{
		key.cmdString = "\n Joint : X ( Zero pose )\n";

		int targetCurrent[4] = { 80,80,80,80 };
		for (int i = 0; i < MAX_FINGER_JOINT_COUNT; i++)
		{
			SetTargetCurrentFinger(targetCurrent, i);
		}
	}
	else if (key.currentCommand == '5')
	{
		key.cmdString = "\n Set Target Current Base\n";

		int targetCurrent[2] = { 80,80 };
		SetTargetCurrentBase(targetCurrent);
	}
	else if (key.currentCommand == 'x')
	{
		key.cmdString = "\n Joint : X ( Zero pose )\n";

		int targetCurrent[20] = { 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 };

		SetTargetCurrentAll(targetCurrent);
	}
	else
	{
		str->append(format("[c] : return\n[1] : Set Current Control Mode On\n[2] :Set Current Control Mode Off \n[3] : Set Target Current 50\n[4] : Set Target Current 80\n[5] : Set Target Base 80 ( DG-4F-M )\n[x] : Zero pose\n"));
	}
	key.currentCommand = NULL;
}

void GraspCommand(string* str)
{
	if (key.graspCommand == 'c')
	{
		key.mainCommand = NULL;
		key.cmdString = "";
		modeCommand = 0;
	}
	else if (key.graspCommand == 'g')
	{
		StartGraspMotion(1);
		key.cmdString = "\n Grasp Object\n";
	}
	else if (key.graspCommand == 'r')
	{
		StartGraspMotion(0);
		key.cmdString = "\n Release Object\n";
	}
	else if (key.graspCommand == '1')
	{
		float force = 5;
		int graspOption = DG_GRASP_OPTION_NONE;				// DG_GRASP_OPTION_FIX_TILT, DG_GRASP_OPTION_PARALLEL
		int smoothGrasping = 0;
		SetGraspData(DG_GRASP_MODE_5F_5FINGER, force, graspOption, smoothGrasping);

		for (int i = 0; i < MAX_JOINT_COUNT; i++) SetPositionModeJoint(0, i);

		key.cmdString = "\n Set GraspData\n";
	}
	else if (key.graspCommand == '2')
	{
		float force = 5;
		int graspOption = DG_GRASP_OPTION_NONE;				// DG_GRASP_OPTION_FIX_TILT, DG_GRASP_OPTION_PARALLEL
		int smoothGrasping = 0;
		SetGraspData(DG_GRASP_MODE_5F_3FINGER, force, graspOption, smoothGrasping);

		int pos[20] = { 1,0,0,0, 1,0,0,0, 1,0,0,0, 1,1,1,1, 1,1,1,1 };
		SetPositionModeAll(pos);

		key.cmdString = "\n Set PositionModeAll\n";
	}
	else if (key.graspCommand == '3')
	{
		float force = 5;
		int graspOption = DG_GRASP_OPTION_NONE;				// DG_GRASP_OPTION_FIX_TILT, DG_GRASP_OPTION_PARALLEL
		int smoothGrasping = 0;
		SetGraspData(DG_GRASP_MODE_5F_2FINGER_1_AND_2, force, graspOption, smoothGrasping);

		int pos[4] = { 1,1,1,1 };

		SetPositionModeFinger(pos, 3);
		SetPositionModeFinger(pos, 4);
		SetPositionModeFinger(pos, 5);

		key.cmdString = "\n Set PositionModeFinger\n";
	}
	else if (key.graspCommand == '4')
	{
		float force = 5;
		int graspOption = DG_GRASP_OPTION_NONE;				// DG_GRASP_OPTION_FIX_TILT, DG_GRASP_OPTION_PARALLEL
		int smoothGrasping = 0;
		SetGraspData(DG_GRASP_MODE_4F_2FINGER_1_AND_2, force, graspOption, smoothGrasping);

		int pos[2] = { 1,1 };

		SetPositionModeBase(pos);

		key.cmdString = "\n Set PositionModeBase\n";
	}
	else if (key.graspCommand == 'f')
	{
		float force = 10;
		SetGraspForce(force);
		key.cmdString = "\n Set GraspForce\n";
	}
	else
	{
		str->append(format("[c] : return\n[g] : Start Grasp Motion\n[r] : Release\n[f] : Set Grasp Force\n[1] : Set Grasp Data\n[2] : Set Position Mode All\n[3] : Set Position Mode Finger\n[4] Set Position Mode Base ( DG-4F-M )"));

		str->append(key.cmdString);
	}
	key.graspCommand = NULL;
}

void ManipulationCommand(string* str)
{
	float offset[6] = { 0,0,0,0,0,0 };
	int step = 1000;

	if (key.manipulationCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.manipulationCommand == 's')
	{
		float P[9];
		float D[9];
		float kI[9];
		float ILimit[9];

		for (int i = 0; i < 9; i++)
		{
			P[i] = 6;
			D[i] = 50;
			kI[i] = 0.012;
			ILimit[i] = 0.1;
		}

		SetManipulationGainPIDAll(P, D, kI, ILimit);
	}
	else if (key.manipulationCommand == 'g')
	{
		float gf = 6;
		SetGraspData(DG_GRASP_MODE_3F_3FINGER, gf, 0, 1);
		StartGraspMotion(1);
		str->append("\nGrasp \n");
	}
	else if (key.manipulationCommand == 'm')
	{
		memcpy(pos, gripperData.joint, sizeof(float) * 12);
		InHandManipulation(offset, 1);
		str->append("\nManipulate \n");
	}
	else if (key.manipulationCommand == 'w')
	{
		offset[0] = 15;
		str->append("\nMove : +X \n");
		InHandManipulation(offset, step);
	}
	else if (key.manipulationCommand == 's')
	{
		offset[0] = -15;
		str->append("\nMove : -X \n");
		InHandManipulation(offset, step);
	}
	else if (key.manipulationCommand == 'a')
	{
		offset[1] = 15;
		str->append("\nMove : +Y \n");
		InHandManipulation(offset, step);
	}
	else if (key.manipulationCommand == 'd')
	{
		offset[1] = -15;
		str->append("\nMove : -Y \n");
		InHandManipulation(offset, step);
	}
	else if (key.manipulationCommand == 'q')
	{
		offset[2] = 15;
		str->append("\nMove : +Z \n");
		InHandManipulation(offset, step);
	}
	else if (key.manipulationCommand == 'e')
	{
		offset[2] = -15;
		str->append("\nMove : -Z \n");
		InHandManipulation(offset, step);
	}
	else if (key.manipulationCommand == '0')
	{
		str->append("\nMove : -Z \n");
		InHandManipulation(offset, step);
	}
	else
	{
		str->append(format("[c] : return\n[s] : Set Manipulation GainPID All\n[g] : Start Grasp Motion\n[m] : In-Hand Manipulation\n[w] : +X\n[s] : -X\n[a] : +Y\n[d] : -Y\n[q] : +Z\n[e] : -Z\n[0] : Move Center\n"));
	}
	key.manipulationCommand = NULL;
}

void GainCommand(string* str)
{
	if (key.gainCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.gainCommand == 'p')
	{
		SetControlPIDMode(0);
		str->append("\nSet PD Control \n");
	}
	else if (key.gainCommand == 'h')
	{
		SetControlPIDMode(1);
		str->append("\nSet PID Control \n");
	}
	else if (key.gainCommand == '1')
	{
		float gainP, gainD, gainI, iLimit;

		gainP = 3;
		gainD = 10;
		gainI = 0.001;
		iLimit = 0.5;

		for (int i = 0; i < MAX_JOINT_COUNT; i++)
		{
			SetJointGainP(gainP, i);
			SetJointGainD(gainD, i);
			SetJointGainI(gainI, iLimit, i);
		}

		str->append("\nSet SetJointGains \n");
	}
	else if (key.gainCommand == '2')
	{
		float gainP[MAX_FINGER_JOINT_COUNT] = { 1.5, 1.5, 1.5, 1.5 };
		float gainD[MAX_FINGER_JOINT_COUNT] = { 6, 6, 6, 6 };
		float gainI[MAX_FINGER_JOINT_COUNT] = { 0.001, 0.001, 0.001, 0.001 };
		float iLimit[MAX_FINGER_JOINT_COUNT] = { 0.5, 0.5, 0.5, 0.5 };

		for (int i = 0; i < MAX_FINGER_COUNT; i++)
		{
			SetJointGainPFinger(gainP, i);
			SetJointGainDFinger(gainD, i);
			SetJointGainIFinger(gainI, iLimit, i);
		}
		str->append("\nSet SetJointGainFingers \n");
	}
	else if (key.gainCommand == '3')
	{

		float gainP[4] = { 0.4,0.4,0.4,0.4 };
		float gainD[4] = { 1,1,1,1 };
		float gainI[4] = { 0,0,0,0 };
		float iLimit[4] = { 0,0,0,0 };

		SetJointGainPIDFinger(gainP, gainD, gainI, iLimit, 1);

		str->append("\nSet SetJointGainPIDFinger \n");
	}
	else if (key.gainCommand == '4')
	{
		float gainP[MAX_JOINT_COUNT];
		float gainD[MAX_JOINT_COUNT];
		float gainI[MAX_JOINT_COUNT];
		float iLimit[MAX_JOINT_COUNT];

		for (int i = 0; i < MAX_JOINT_COUNT; i++)
		{
			gainP[i] = 1;
			gainD[i] = 3;
			gainI[i] = 0.001;
			iLimit[i] = 0.5;
		}

		SetJointGainPIDAll(gainP, gainD, gainI, iLimit);
		str->append("\nSet SetJointGainPIDAll \n");
	}
	else if (key.gainCommand == '5')
	{
		float gainP, gainD, gainI, iLimit;

		gainP = 0.4;
		gainD = 1;
		gainI = 0;
		iLimit = 0;

		SetJointGainPIDAllEqual(gainP, gainD, gainI, iLimit);

		str->append("\nSet SetJointGainPIDAllEqual \n");
	}
	else if (key.gainCommand == '6')
	{
		float gainP[MAX_BASE_JOINT_COUNT] = { 1.5, 1.5 };
		float gainD[MAX_BASE_JOINT_COUNT] = { 6, 6 };
		float gainI[MAX_BASE_JOINT_COUNT] = { 0.001, 0.001 };
		float iLimit[MAX_BASE_JOINT_COUNT] = { 0.5, 0.5 };

		SetJointGainPBase(gainP);
		SetJointGainDBase(gainD);
		SetJointGainIBase(gainI, iLimit);

		str->append("\nSet SetJointGainBase \n");
	}
	else if (key.gainCommand == '7')
	{
		float gainP[MAX_BASE_JOINT_COUNT] = { 1.5, 1.5 };
		float gainD[MAX_BASE_JOINT_COUNT] = { 6, 6 };
		float gainI[MAX_BASE_JOINT_COUNT] = { 0.001, 0.001 };
		float iLimit[MAX_BASE_JOINT_COUNT] = { 0.5, 0.5 };
		
		SetJointGainPIDBase(gainP, gainD, gainI, iLimit);

		str->append("\nSet SetJointGainPIDBase \n");
		}
	else
	{
		str->append(format("[c] : return\n[p] : PD Control\n[h] : PID Control\n[1] : Set Joint Gains\n[2] : Set Joint Gain Fingers\n[3] : Set Joint GainPID Finger\n[4] : Set Joint GainPID All\n[5] : Set Joint GainPID All Equal\n[6] : Set Joint GainP/I/D Base\n[7] : Set Joint GainPID Base"));
	}
	key.gainCommand = NULL;
}

void MotionSetCommand(string* str)
{
	if (key.motionSetCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.motionSetCommand == '1')
	{
		int motionTime = 1;
		for (int i = 0; i < MAX_JOINT_COUNT; i++) SetMotionTimeJoint(motionTime, i);

		str->append("\n Set MotionTimeJoint\n");
	}
	else if (key.motionSetCommand == '2')
	{
		int motionTime[MAX_FINGER_JOINT_COUNT] = { 300,300,300,300 };

		SetMotionTimeFinger(motionTime, 0);
		SetMotionTimeFinger(motionTime, 1);
		SetMotionTimeFinger(motionTime, 2);
		SetMotionTimeFinger(motionTime, 3);
		SetMotionTimeFinger(motionTime, 4);

		str->append("\n Set MotionTimeFinger\n");
	}
	else if (key.motionSetCommand == '3')
	{
		int motionTime[MAX_JOINT_COUNT] = { 800,800,800,800,800,800,800,800,800,800,800,800,800,800,800,800,800,800,800,800 };
		SetMotionTimeAll(motionTime);

		str->append("\n Set SetMotionTimeAll\n");
	}
	else if (key.motionSetCommand == '4')
	{
		int motionTime = 2000;
		SetMotionTimeAllEqual(motionTime);

		str->append("\n Set MotionTimeAllEqual\n");
	}
	else if (key.motionSetCommand == 't')
	{
		int isOn = 1;
		SetTorqueLimitMode(isOn);
		str->append("\n Set TorqueLimitMode\n");
	}
	else if (key.motionSetCommand == 'f')
	{
		SetFingerTipDataZero();
		str->append("\n Set Finger tip sensor Data Zero\n");
	}
	else
	{
		str->append(format("[c] : return\n[1] : Set MotionTime Joint\n[2] : Set MotionTime Finger\n[3] : Set MotionTime All\n[4] : Set MotionTime All Equal\n[t] : Set Torque Limit Mode\n[f] : Set Fingertip Data zero"));
	}
	key.motionSetCommand = NULL;
}

void TCPCommand(string* str)
{
	if (key.TCPCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.TCPCommand == 'x')
	{
		float Tcp[6];
		GetCurrentTcpPose(Tcp);
		str->append("\n Get Current TCP Pose \n");
	}
	else if (key.TCPCommand == '1')
	{
		float gainP[6] = { 100,100,100,1,1,1 };
		float gainD[6] = { 100,100,100,1,1,1 };
		float gainI[6] = { 0.01,0.01,0.01,0.001,0.001,0.001 };
		float iLimit[6] = { 0.5,0.5,0.5,0.05,0.05,0.05 };

		for (int i = 0; i < MAX_FINGER_COUNT; i++)
		{
			SetTCPGainPFinger(gainP, i);
			SetTCPGainDFinger(gainD, i);
			SetTCPGainIFinger(gainI, iLimit, i);
		}
		str->append("\n Set TCP GainP,I,D Finger \n");
	}
	else if (key.TCPCommand == '2')
	{
		float gainP[6 * MAX_FINGER_COUNT];
		float gainD[6 * MAX_FINGER_COUNT];
		float gainI[6 * MAX_FINGER_COUNT];
		float iLimit[6 * MAX_FINGER_COUNT];

		for (int i = 0; i < MAX_FINGER_COUNT; i++)
		{
			for (int j = 0; j < CARTESIAN_COORDINATE_POSE_COUNT / 2; j++)
			{
				/// translation 
				gainP[j + 6 * i] = 50;
				gainD[j + 6 * i] = 100;
				gainI[j + 6 * i] = 0.01;
				iLimit[j + 6 * i] = 0.5;

				/// rotation gain
				gainP[j + 3 + 6 * i] = 1;
				gainD[j + 3 + 6 * i] = 2;
				gainI[j + 3 + 6 * i] = 0.001;
				iLimit[j + 3 + 6 * i] = 0.05;
			}
		}

		SetTCPGainPAll(gainP);
		SetTCPGainDAll(gainD);
		SetTCPGainIAll(gainI, iLimit);

		str->append("\n Set TCP GainP,I,D All\n");
	}
	else if (key.TCPCommand == '3')
	{
		int motionTime = 100;
		for (int i = 0; i < MAX_FINGER_COUNT; i++)
		{
			SetTCPMotionTimeFinger(100, i);
		}
	}
	else if (key.TCPCommand == '4')
	{
		int motionTime[MAX_FINGER_COUNT] = { 200,200,200,200,200 };
		SetTCPMotionTimeAll(motionTime);
	}
	else if (key.TCPCommand == '5')
	{
		int motionTime = 1000;
		SetTCPMotionTimeAllEqual(motionTime);
	}
	else if (key.TCPCommand == 'l')
	{
		float tcp[CARTESIAN_COORDINATE_POSE_COUNT * MAX_FINGER_COUNT];
		memcpy(tcp, gripperData.TCP, sizeof(tcp));

		for (int i = 0; i < MAX_FINGER_COUNT; i++)
		{
			MoveTCPFinger(tcp + 6 * i, i);
		}
	}
	else if (key.TCPCommand == 'a')
	{
		float tcp[CARTESIAN_COORDINATE_POSE_COUNT * MAX_FINGER_COUNT];
		memcpy(tcp, gripperData.TCP, sizeof(tcp));

		MoveTCPAll(tcp);
	}
	else
	{
		str->append(format("[c] : return\n[x] : Get Current TCP Pose\n[l] : MoveTCPFinger\n[a] : MoveTCPAll\n[1] : Set TCPGainPIDFinger\n[2] : Set TCPGainPIDAll\n[3] : Set TCPMotionTimeFinger\n[4] : Set TCPMotionTimeAll\n[5] : Set TCPMotionTimeAllEqual"));
	}
	key.TCPCommand = NULL;
}

void RecipeCommand(string* str)
{
	int idx = 0;

	if (key.recipeCommand == 'c')
	{
		key.mainCommand = NULL;
		modeCommand = 0;
	}
	else if (key.recipeCommand == 'b')
	{
		RecipeBlendData blendData;

		blendData.number = 1;
		blendData.blendWaitTime = 100;
		blendData.recipeGainNumber = 1;
		blendData.recipePoseNumber = 2;

		int blendNumber = 2;
		ClearMoveBlendJoint();
		UpdateBlendJoint(blendData);
		SetMoveBlendJoint(blendNumber);
		AddMoveBlendJoint();

		key.cmdString = "\n Set UpdateBlendJoint\n";
	}
	else if (key.recipeCommand == 'm')
	{
		int blendNumber = 1;
		StartMoveBlendJoint(blendNumber);

		key.cmdString = "\n Start Move Blend Joint\n";
	}
	else if (key.recipeCommand == 'o')
	{
		StopMoveBlendJoint();
		key.cmdString = "\n Stop Move Blend Joint\n";
	}
	else if (key.recipeCommand == '4')
	{
		int poseNumber = 1;

		UpdateRecipeCurrentPoseData(poseNumber);
		key.cmdString = "\n Update Recipe Current Pose Data\n";
	}
	else if (key.recipeCommand == '5')
	{
		int poseNumber = 1;
		float joint[20] = { 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
		MoveJointAll(joint);
		UpdateRecipeTargetPoseData(poseNumber);
		key.cmdString = "\n Update Recipe Target Pose Data\n";
	}
	else if (key.recipeCommand == '6')
	{
		int poseNumber = 1;
		LoadRecipePoseData(poseNumber);
		key.cmdString = "\n Load Recipe Pose Data\n";
	}
	else if (key.recipeCommand == '7')
	{
		int gainNumber = 1;
		float p = 1.5;
		float d = 2;
		float i = 0;
		float iLimit = 0;
		SetJointGainPIDAllEqual(p, i, d, iLimit);
		UpdateRecipeGainData(gainNumber);
		key.cmdString = "\n Update Recipe Current Gain Data\n";
	}
	else if (key.recipeCommand == '8')
	{
		int gainNumber = 1;
		LoadRecipeGainData(gainNumber);
		key.cmdString = "\n Load Recipe Gain Data\n";
	}
	else if (key.recipeCommand == '9')
	{
		int graspNumber = 1;
		DG_GRASP_MODE graspMode = DG_GRASP_MODE_5F_5FINGER;
		float force = 5;
		int smoothGrasp = 0;
		int graspOption = 0;
		int positionMode[20] = { 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };

		SetPositionModeAll(positionMode);
		SetGraspData(graspMode, force, graspOption, smoothGrasp);
		UpdateRecipeGraspData(graspNumber);
		key.cmdString = "\n Update Recipe Current Grasp Data\n";
	}
	else if (key.recipeCommand == '0')
	{
		int graspNumber = 1;
		LoadRecipeGraspData(graspNumber);
		key.cmdString = "\n Load Recipe Grasp Data\n";
	}
	else
	{
		str->append(format("[c] : return\n[b] : Set UpdateBlendJoint\n[m] : Start Move Blend Joint\n[o] : Stop Move Blend Joint\n[4] : Update Recipe Current Pose Data\n[5] : Update Recipe Target Pose Data\n[6] : Load Recipe Pose Data\n[7] : Update Recipe Current Gain Data\n[8] : Load Recipe Gain Data\n[9] : Update Recipe Current Grasp Data\n[0] : Load Recipe Grasp Data\n"));
	}
	key.recipeCommand = NULL;
}
