/*
 * post-processing: solution validation and metrics
 */
#pragma once
#include "instance.hpp"
#include "reservation.hpp"

// check that a solution is collision-free and well-formed
bool is_feasible_solution(const HetInstance& ins,
                          const ReservationTable& P,
                          int verbose = 0);

int get_makespan(const ReservationTable& P, int N,
                 const std::unordered_map<int, int>& goal_time = {});
int get_sum_of_costs(const ReservationTable& P, const HetInstance& ins,
                     const std::unordered_map<int, int>& goal_time = {});

void print_stats(int verbose, const HetInstance& ins,
                 const ReservationTable& P, double comp_time_ms,
                 const std::unordered_map<int, int>& goal_time = {});

void make_log(const HetInstance& ins, const ReservationTable& P,
              const std::string& output_file, double comp_time_ms,
              const std::string& map_name, int seed,
              const std::unordered_map<int, int>& goal_time = {});
