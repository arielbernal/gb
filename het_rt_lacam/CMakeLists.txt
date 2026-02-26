cmake_minimum_required(VERSION 3.16)
project(het_rt_lacam CXX)

# library
add_subdirectory(het_rt_lacam)
add_subdirectory(third_party/argparse)

# main executable
add_executable(main main.cpp)
target_link_libraries(main het_rt_lacam argparse)

# tests
add_subdirectory(third_party/googletest)
add_executable(test_all
  tests/test_graph.cpp
  tests/test_instance.cpp
  tests/test_pibt.cpp
  tests/test_planner.cpp
)
target_link_libraries(test_all het_rt_lacam gtest_main)
enable_testing()
add_test(NAME test_all COMMAND test_all)
