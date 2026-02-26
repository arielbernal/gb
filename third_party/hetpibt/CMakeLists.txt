cmake_minimum_required(VERSION 3.16)
project(hetpibt-project CXX)

add_subdirectory(./hetpibt)
add_subdirectory(../lacam/third_party/argparse ${CMAKE_BINARY_DIR}/argparse)
add_subdirectory(../lacam/third_party/googletest ${CMAKE_BINARY_DIR}/googletest)

add_executable(main main.cpp)
target_compile_features(main PUBLIC cxx_std_17)
target_link_libraries(main hetpibt argparse)

# tests
set(TEST_MAIN_FUNC ../lacam/third_party/googletest/googletest/src/gtest_main.cc)
set(TEST_ALL_SRC ${TEST_MAIN_FUNC})
macro(add_test name target)
  add_executable(${name} ${target} ${TEST_MAIN_FUNC})
  target_link_libraries(${name} hetpibt gtest)
  list(APPEND TEST_ALL_SRC ${target})
endmacro(add_test)

add_test(test_graph ./tests/test_graph.cpp)
add_test(test_fleet ./tests/test_fleet.cpp)
add_test(test_reservation ./tests/test_reservation.cpp)
add_test(test_planner ./tests/test_planner.cpp)

add_executable(test_all ${TEST_ALL_SRC})
target_link_libraries(test_all hetpibt gtest)
