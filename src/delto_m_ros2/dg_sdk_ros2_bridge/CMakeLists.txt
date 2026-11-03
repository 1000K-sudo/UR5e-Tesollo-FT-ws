# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
cmake_minimum_required(VERSION 3.8)
project(dg_sdk_ros2_bridge)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(dg_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# Include directories
include_directories(
  include
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Add executable
add_executable(dg_sdk_ros2_bridge_node
  src/dg_sdk_ros2_bridge_node.cpp
)

# Link libraries
target_link_libraries(dg_sdk_ros2_bridge_node
  ${CMAKE_CURRENT_SOURCE_DIR}/libs/libDGSDK_171.so
)

# Target dependencies
ament_target_dependencies(dg_sdk_ros2_bridge_node
  rclcpp
  dg_msgs
  std_msgs
)

# Install executable
install(TARGETS
  dg_sdk_ros2_bridge_node
  DESTINATION lib/${PROJECT_NAME}
)

# Install headers
install(DIRECTORY include/
  DESTINATION include/
  FILES_MATCHING PATTERN "*.h"
)

# Install shared library
install(FILES libs/libDGSDK_171.so
  DESTINATION lib
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()