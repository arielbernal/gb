/*
 * solution evaluation metrics
 */

#pragma once

#include "dist_table.hpp"
#include "instance.hpp"
#include "utils.hpp"

int get_makespan(const Solution &solution);

int get_path_cost(const Solution &solution, int i);  // single-agent path cost
int get_sum_of_costs(const Solution &solution);

int get_sum_of_loss(const Solution &solution);

int get_makespan_lower_bound(const Instance &ins, DistTable &D);
int get_sum_of_costs_lower_bound(const Instance &ins, DistTable &D);
