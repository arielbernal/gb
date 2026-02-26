#!/bin/bash
# Convert all 105 scenarios to het_bench format, then run hetpibt on all 100.
set -e

MAPS_DIR="E:/gb/benchmarks/maps"
SCEN_DIR="E:/gb/benchmarks/scenarios"
CONVERTER="E:/gb/benchmarks/generators/convert_to_hetbench.py"
HETPIBT="E:/gb/hetpibt/build/Release/main.exe"
OUTFILE="E:/gb/benchmarks/results/hetpibt_all_105_feb25.csv"

MAP_TYPES=("cooperative_clearing_105" "bottleneck_doors_105" "corridor_speed_105" "intersection_105")

# Step 1: Convert all scenarios to het_bench format
echo "=== Converting scenarios ==="
for mt in "${MAP_TYPES[@]}"; do
    map_file="${MAPS_DIR}/${mt}.map"
    for seed in $(seq -w 0 24); do
        scen="${SCEN_DIR}/${mt}_${seed}.scen"
        hb="${SCEN_DIR}/${mt}_${seed}_hb.scen"
        if [ ! -f "$hb" ]; then
            python "$CONVERTER" --scen "$scen" --map "$map_file" --output "$hb"
        fi
    done
done
echo "Conversion done."

# Step 2: Run hetpibt on all 100 scenarios
echo "=== Running hetpibt ==="
echo "map_type,seed,goals_reached,goals_total,goal_pct,SOC,makespan,time_ms" > "$OUTFILE"

for mt in "${MAP_TYPES[@]}"; do
    map_file="${MAPS_DIR}/${mt}.map"
    for seed in $(seq -w 0 24); do
        hb="${SCEN_DIR}/${mt}_${seed}_hb.scen"
        echo -n "  ${mt}_${seed} ... "

        output=$("$HETPIBT" -m "$map_file" -s "$hb" -t 60 2>&1) || true

        # Parse output
        goals_reached=$(echo "$output" | grep -oP 'goals_reached=\K[0-9]+(?=/)') || goals_reached=0
        goals_total=$(echo "$output" | grep -oP 'goals_reached=[0-9]+/\K[0-9]+') || goals_total=0
        soc=$(echo "$output" | grep -oP 'sum_of_costs=\K[0-9]+') || soc=0
        makespan=$(echo "$output" | grep -oP 'makespan=\K[0-9]+') || makespan=0
        time_ms=$(echo "$output" | grep -oP 'comp_time\(ms\)=\K[0-9]+') || time_ms=0

        if [ "$goals_total" -gt 0 ]; then
            goal_pct=$(awk "BEGIN {printf \"%.1f\", 100.0 * $goals_reached / $goals_total}")
        else
            goal_pct="0.0"
        fi

        echo "${goals_reached}/${goals_total} (${goal_pct}%) SOC=${soc} T=${time_ms}ms"
        echo "${mt},${seed},${goals_reached},${goals_total},${goal_pct},${soc},${makespan},${time_ms}" >> "$OUTFILE"
    done
done

echo ""
echo "Results saved to: $OUTFILE"
echo "=== Done ==="
