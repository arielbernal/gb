# Money Plot — Instance Solve Rate (Apples-to-Apples)

**Metric:** Instance solve % = fraction of seeds where ALL agents reached their goals.
Same metric for both solvers. Directly comparable.

**Sources:**
- HetPIBT N=5-20: `hetpibt_scaling_feb25.csv` + `hetpibt_scaling_corr_bn_feb25.csv` (5 seeds each)
- HetPIBT N=25: `hetpibt_all_105_feb25.csv` (25 seeds)
- Het-LaCAM: user-provided scaling data from `het_lacam_scaling_all4maps_feb26.csv`

## Combined Table

| Map | Agents | Het-LaCAM solve% | HetPIBT solve% |
|-----|--------|-------------------|----------------|
| corridor_speed | 5 | 100% | 0% |
| corridor_speed | 10 | 100% | 0% |
| corridor_speed | 15 | 100% | 0% |
| corridor_speed | 20 | 88% | 0% |
| corridor_speed | 25 | 84% | 0% |
| bottleneck_doors | 5 | 100% | 100% |
| bottleneck_doors | 10 | 100% | 100% |
| bottleneck_doors | 15 | 100% | 80% |
| bottleneck_doors | 20 | 88% | 60% |
| bottleneck_doors | 25 | 84% | 64% |
| intersection | 5 | 100% | 40% |
| intersection | 10 | 76% | 0% |
| intersection | 15 | 60% | 0% |
| intersection | 20 | 36% | 0% |
| intersection | 25 | 12% | 0% |
| cooperative_clearing | 5 | 100% | 20% |
| cooperative_clearing | 10 | 72% | 0% |
| cooperative_clearing | 15 | 40% | 0% |
| cooperative_clearing | 20 | 20% | 0% |
| cooperative_clearing | 25 | 16% | 0% |

## Per-Map Summary

### corridor_speed
Het-LaCAM: 100% → 84%. HetPIBT: 0% at all agent counts.
Bidirectional corridor traffic is impossible for PIBT to fully resolve.

### bottleneck_doors
Het-LaCAM: 100% → 84%. HetPIBT: 100% → 64%.
HetPIBT's strongest map. Both solvers degrade similarly at high density.
Competitive gap is only 20-28pp at N=20-25.

### intersection
Het-LaCAM: 100% → 12%. HetPIBT: 40% → 0%.
Both struggle as agents increase. Het-LaCAM retains partial success longer.
HetPIBT collapses to 0% at N>=10.

### cooperative_clearing
Het-LaCAM: 100% → 16%. HetPIBT: 20% → 0%.
Hardest map for both. Narrow passage creates deadlocks.
HetPIBT collapses to 0% at N>=10.

## Key Takeaway

On the instance-solve metric, Het-LaCAM dominates across all maps and agent counts. HetPIBT is only competitive on bottleneck_doors (100% vs 100% at N<=10, 64% vs 84% at N=25). On the other three maps, HetPIBT's instance-solve rate is 0% for N>=10, while Het-LaCAM maintains 12-84%.

The tradeoff is compute: HetPIBT runs in ~60ms vs Het-LaCAM's 60s timeout, making it 100-1000x faster per instance.
