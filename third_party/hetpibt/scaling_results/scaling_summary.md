# HetPIBT Scaling Results

## Experiment Setup

- **Map**: room-64-64-8 (640x640 scaled, MAP_SCALE=10)
- **Fleet types**: cs=1 (50%), cs=6 (30%), cs=11 (20%)
- **Agent counts**: [15, 50, 100, 150, 200]
- **Seeds per count**: 10
- **Max timesteps**: 500 | **Goal lock**: enabled

## Summary Table

| Agents | Placed | Goal% | cs1% | cs6% | cs11% | Avg SOC | Avg Make | Avg Wait% | Avg ms | Stuck | NoMove |
|--------|--------|-------|------|------|-------|---------|----------|-----------|--------|-------|--------|
|     15 |    15 | 98.7% | 100% |  95% | 100% |    5115 |     1017 |      5.5% |  403.1 |   0.2 |    0.0 |
|     50 |    50 | 93.8% |  97% |  87% |  97% |   15590 |     1937 |      8.4% | 19115.7 |   3.1 |    0.0 |
|    100 |    98 | 71.9% |  69% |  75% |  77% |   21346 |     1275 |     10.1% | 84275.1 |  27.3 |    0.2 |
|    150 |   138 | 35.2% |  28% |  41% |  53% |    8336 |      391 |     21.2% | 108460.4 |  75.4 |    0.5 |
|    200 |   178 | 22.5% |  17% |  22% |  53% |    5476 |      267 |     25.9% | 96352.8 | 102.3 |    0.2 |

## Breaking Points

- **Below 90% success**: first at N=100 (avg 71.9%)
- **Below 75% success**: first at N=100 (avg 71.9%)
- **Below 50% success**: first at N=150 (avg 35.2%)

## Per-Fleet Failure Analysis

Which fleet types fail first as congestion increases?

### N=15
- cs=1 (small): 100.0% goals reached
- cs=6 (medium): 95.0% goals reached
- cs=11 (large): 100.0% goals reached
- Avg stuck agents: 0.2
- Avg no-move (deadlocked): 0.0

### N=50
- cs=1 (small): 96.8% goals reached
- cs=6 (medium): 86.7% goals reached
- cs=11 (large): 97.0% goals reached
- Avg stuck agents: 3.1
- Avg no-move (deadlocked): 0.0

### N=100
- cs=1 (small): 68.6% goals reached
- cs=6 (medium): 75.3% goals reached
- cs=11 (large): 76.7% goals reached
- Avg stuck agents: 27.3
- Avg no-move (deadlocked): 0.2

### N=150
- cs=1 (small): 27.9% goals reached
- cs=6 (medium): 40.7% goals reached
- cs=11 (large): 53.3% goals reached
- Avg stuck agents: 75.4
- Avg no-move (deadlocked): 0.5

### N=200
- cs=1 (small): 17.1% goals reached
- cs=6 (medium): 22.5% goals reached
- cs=11 (large): 52.8% goals reached
- Avg stuck agents: 102.3
- Avg no-move (deadlocked): 0.2

## Performance Scaling

| Agents | Avg comp time (ms) | Avg makespan |
|--------|--------------------|--------------|
|     15 |              403.1 |         1017 |
|     50 |            19115.7 |         1937 |
|    100 |            84275.1 |         1275 |
|    150 |           108460.4 |          391 |
|    200 |            96352.8 |          267 |

## Failure Mode Analysis

### Deadlocks vs Timeouts

- **No-move agents**: agents that stayed at their start position for the entire simulation (likely deadlocked)
- **Stuck agents**: agents that made some progress but didn't reach their goal (ran out of timesteps or couldn't navigate congestion)

**N=15**: 0 deadlocked (no-move), 2 stuck-but-moved, across 10 runs
**N=50**: 0 deadlocked (no-move), 31 stuck-but-moved, across 10 runs
**N=100**: 2 deadlocked (no-move), 271 stuck-but-moved, across 10 runs
**N=150**: 5 deadlocked (no-move), 749 stuck-but-moved, across 10 runs
**N=200**: 2 deadlocked (no-move), 1021 stuck-but-moved, across 10 runs

### Fleet Type Interaction Failures

Large agents (cs=11) occupying 121 base cells create bottlenecks that block smaller agents. The stuck-per-fleet breakdown shows which fleet types are most affected by congestion.

| Agents | Stuck cs=1 | Stuck cs=6 | Stuck cs=11 |
|--------|------------|------------|-------------|
|     15 |        0.0 |        0.2 |         0.0 |
|     50 |        0.8 |        2.0 |         0.3 |
|    100 |       15.7 |        7.4 |         4.2 |
|    150 |       46.6 |       22.2 |         6.6 |
|    200 |       62.9 |       34.5 |         4.9 |
