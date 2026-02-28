cmake_minimum_required(VERSION 3.16)

add_library(het_rt_lacam STATIC
  src/dist_table.cpp
  src/graph.cpp
  src/heuristic.cpp
  src/hnode.cpp
  src/instance.cpp
  src/lacam.cpp
  src/lnode.cpp
  src/metrics.cpp
  src/pibt.cpp
  src/planner.cpp
  src/post_processing.cpp
  src/st_reservation.cpp
  src/utils.cpp
)

target_compile_features(het_rt_lacam PUBLIC cxx_std_17)
target_include_directories(het_rt_lacam PUBLIC include)

if(MSVC)
  target_compile_options(het_rt_lacam PRIVATE /W3 /permissive-)
else()
  target_compile_options(het_rt_lacam PRIVATE -O3 -Wall)
endif()

find_package(Threads REQUIRED)
target_link_libraries(het_rt_lacam PUBLIC Threads::Threads)
