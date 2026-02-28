# RT-LaCAM Full Benchmark Analysis
Date: Feb 27, 2026 | Settings: --rt --rt-budget 100 --goal-lock -t 60

## Overall: RT 98/190 | STD 94/190 | hetpibt 120/190

## 1. Solve Rate: Category × Agent Count

| Category | Agents | RT | STD | hetpibt | Total |
|----------|--------|----|-----|---------|-------|
| bottleneck_doors | n5 | 5/5 | 5/5 | 5/5 | 5 |
| bottleneck_doors | n10 | 4/5 | 4/5 | 5/5 | 5 |
| bottleneck_doors | n15 | 3/5 | 3/5 | 4/5 | 5 |
| bottleneck_doors | n20 | 4/5 | 4/5 | 2/5 | 5 |
| bottleneck_doors | n25 | 19/25 | 19/25 | 8/25 | 25 |
| **bottleneck_doors total** | | **35/45** | **35/45** | **24/45** | 45 |
| corridor_speed | n5 | 5/5 | 5/5 | 5/5 | 5 |
| corridor_speed | n10 | 4/5 | 4/5 | 5/5 | 5 |
| corridor_speed | n15 | 2/5 | 2/5 | 4/5 | 5 |
| corridor_speed | n20 | 0/5 | 0/5 | 4/5 | 5 |
| corridor_speed | n25 | 13/25 | 12/25 | 16/25 | 25 |
| **corridor_speed total** | | **24/45** | **23/45** | **34/45** | 45 |
| intersection | n5 | 5/5 | 5/5 | 5/5 | 5 |
| intersection | n10 | 3/5 | 3/5 | 5/5 | 5 |
| intersection | n15 | 0/5 | 0/5 | 1/5 | 5 |
| intersection | n20 | 0/5 | 0/5 | 1/5 | 5 |
| intersection | n25 | 0/25 | 0/25 | 3/25 | 25 |
| **intersection total** | | **8/45** | **8/45** | **15/45** | 45 |
| cooperative_clearing | n5 | 5/5 | 5/5 | 5/5 | 5 |
| cooperative_clearing | n10 | 5/5 | 5/5 | 5/5 | 5 |
| cooperative_clearing | n15 | 4/5 | 3/5 | 5/5 | 5 |
| cooperative_clearing | n20 | 2/5 | 2/5 | 4/5 | 5 |
| cooperative_clearing | n25 | 6/25 | 5/25 | 19/25 | 25 |
| **cooperative_clearing total** | | **22/45** | **20/45** | **38/45** | 45 |
| het_bench | var | 9/10 | 8/10 | 9/10 | 10 |
| **het_bench total** | | **9/10** | **8/10** | **9/10** | 10 |
| **GRAND TOTAL** | | **98/190** | **94/190** | **120/190** | 190 |

## 2. SOC Quality: RT vs hetpibt (mutually solved)

- Mutually solved: 71 scenarios
- RT/hetpibt SOC ratio: mean=15.56x, median=7.10x, min=1.69x, max=79.63x
- (ratio > 1 means RT has higher SOC = worse quality)

### RT vs STD SOC (mutually solved)
- Mutually solved: 94 scenarios
- RT/STD SOC ratio: mean=1.09x, median=1.02x
- (ratio > 1 means RT has higher SOC than STD anytime search)

## 3. Exclusive Solves

### RT solves but STD doesn't (4 scenarios)
- cooperative_clearing/n15/scen03: steps=1227 SOC=16298 t=31400ms
- cooperative_clearing/n25/scen15: steps=3605 SOC=81131 t=52318ms
- corridor_speed/n25/scen22: steps=3359 SOC=41435 t=36200ms
- het_bench/var/scen9: steps=194 SOC=507 t=476ms

### STD solves but RT doesn't (0 scenarios) — REGRESSIONS

### RT solves but hetpibt doesn't (26 scenarios)
- bottleneck_doors/n15/scen00
- bottleneck_doors/n20/scen01
- bottleneck_doors/n20/scen04
- bottleneck_doors/n25/scen00
- bottleneck_doors/n25/scen04
- bottleneck_doors/n25/scen07
- bottleneck_doors/n25/scen08
- bottleneck_doors/n25/scen10
- bottleneck_doors/n25/scen12
- bottleneck_doors/n25/scen13
- bottleneck_doors/n25/scen14
- bottleneck_doors/n25/scen16
- bottleneck_doors/n25/scen17
- bottleneck_doors/n25/scen18
- bottleneck_doors/n25/scen20
- bottleneck_doors/n25/scen23
- bottleneck_doors/n25/scen24
- cooperative_clearing/n25/scen02
- cooperative_clearing/n25/scen22
- corridor_speed/n15/scen01
- corridor_speed/n25/scen01
- corridor_speed/n25/scen05
- corridor_speed/n25/scen11
- corridor_speed/n25/scen12
- corridor_speed/n25/scen17
- corridor_speed/n25/scen24

### hetpibt solves but RT doesn't (48 scenarios)
- bottleneck_doors/n10/scen01
- bottleneck_doors/n15/scen01
- bottleneck_doors/n15/scen02
- bottleneck_doors/n25/scen03
- bottleneck_doors/n25/scen05
- bottleneck_doors/n25/scen19
- cooperative_clearing/n15/scen04
- cooperative_clearing/n20/scen02
- cooperative_clearing/n20/scen04
- cooperative_clearing/n25/scen00
- cooperative_clearing/n25/scen01
- cooperative_clearing/n25/scen03
- cooperative_clearing/n25/scen04
- cooperative_clearing/n25/scen06
- cooperative_clearing/n25/scen07
- cooperative_clearing/n25/scen09
- cooperative_clearing/n25/scen10
- cooperative_clearing/n25/scen11
- cooperative_clearing/n25/scen13
- cooperative_clearing/n25/scen16
- cooperative_clearing/n25/scen18
- cooperative_clearing/n25/scen19
- cooperative_clearing/n25/scen20
- cooperative_clearing/n25/scen21
- corridor_speed/n10/scen04
- corridor_speed/n15/scen00
- corridor_speed/n15/scen02
- corridor_speed/n15/scen04
- corridor_speed/n20/scen00
- corridor_speed/n20/scen02
- corridor_speed/n20/scen03
- corridor_speed/n20/scen04
- corridor_speed/n25/scen00
- corridor_speed/n25/scen02
- corridor_speed/n25/scen03
- corridor_speed/n25/scen06
- corridor_speed/n25/scen08
- corridor_speed/n25/scen09
- corridor_speed/n25/scen13
- corridor_speed/n25/scen15
- corridor_speed/n25/scen21
- intersection/n10/scen03
- intersection/n10/scen04
- intersection/n15/scen04
- intersection/n20/scen04
- intersection/n25/scen04
- intersection/n25/scen12
- intersection/n25/scen19

## 4. Runtime Comparison (solved scenarios only)

- **RT**: n=98, mean=4010ms, median=1335ms, p95=20757ms, max=52318ms
- **STD**: n=94, mean=29996ms, median=30408ms, p95=31429ms, max=31867ms
- **hetpibt**: n=120, mean=96ms, median=68ms, p95=144ms, max=1505ms

### RT Step Counts (solved)
- n=98, mean=535, median=329, max=3605
