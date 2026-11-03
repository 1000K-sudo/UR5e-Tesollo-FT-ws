# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================

cmake_minimum_required(VERSION 3.10)
project(TesolloSDKTools CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/DGSDK
    /usr/local/include
)

link_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/DGSDK
    /usr/local/lib
)

add_executable(tesollo_cmd tesollo_cmd.cpp)
target_link_libraries(tesollo_cmd DGSDK pthread)

add_executable(simple_test DGSDK/simple_test.cpp)
target_link_libraries(simple_test DGSDK pthread)
