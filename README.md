# CS202 Group Project: RCPSP Solver

Resource-Constrained Project Scheduling Problem solver submitted for CS202.

## Team

| Name | Student ID |
| ---- | ---------- |
| CHRISTOPHER TJANDRA | 01466084 |
| ONG JIAN RONG CALVIN | 01469754 |
| TAN YONG HAO JEREMY | 01506688 |
| WAI HOI | 01461175 |
| MOHAMED SHAIK AZEEZ | 01511156 |

## Run Command

**For grading / clean output only:**
```
python3 src/main.py sm_j10/PSP1.SCH 2>/dev/null
```
Example output:
```
0, 0, 3, 0, 6, 10, 15, 10, 15, 6
```
Just the comma-separated start times for activities 1 through N. If infeasible, prints `-1`.

**For development / full info (makespan, validity, timing):**
```
python3 src/main.py sm_j10/PSP1.SCH
```
Example output:
```
makespan=25 valid=True time=28.00s
workers=4 approach=alns (Adaptive Large Neighborhood Search + SSGS Decoder)
0, 0, 3, 0, 6, 10, 15, 10, 15, 6
```
The extra info (makespan, valid, time, approach) goes to stderr.

## Requirements

- Python 3
- Standard library only
- Runs within the 30 second time limit per instance

No `pip install` needed.

## Repository Structure

```
src/
  main.py         entry point, handles CLI args and output format
  parser.py       reads .SCH file into Project object
  models.py       Project and Activity dataclasses
  scheduler.py    SSGS core scheduling engine + priority rules (LFT, MTS, GRPW)
  optimizer.py    Genetic Algorithm and ALNS metaheuristics
  validator.py    precedence and resource constraint checks, batch testing
sm_j10/           270 J10 benchmark instances (10 real activities each)
sm_j20/           270 J20 benchmark instances (20 real activities each)
```

## Optional Flags

```
python src/main.py <file.SCH> --approach <ga|alns|lft_ssgs|id_ssgs|topo_seq>
python src/main.py <file.SCH> --time-budget <seconds>
python src/main.py <file.SCH> --workers <num_workers>
python src/main.py --batch <folder>
```

Default is `--approach ALNS` with a 28 second time budget (2 second safety margin from the 30s hard limit).

## How It Works (Short Version)

Full details are in the report. Quick summary:

1. **Parse** the `.SCH` file into a Project object holding activities, precedence dicts, and resource capacities.
2. **Feasibility check**: if any single activity demands more of a resource than the total capacity, output `-1` immediately.
3. **Baseline**: run SSGS with the LFT priority rule to get a guaranteed valid schedule.
4. **Optimise**: run either GA or ALNS for the rest of the time budget, trying thousands of different activity orderings. Each ordering is fed to SSGS which produces a schedule. Keep the best makespan found.

SSGS (Serial Schedule Generation Scheme) is the core. Given any precedence-feasible activity list, it walks through the list and places each activity at the earliest time where all predecessors are done and resources are free. It always produces a valid schedule.

The optimisers (GA and ALNS) only generate different activity lists. They never touch the schedule directly, so validity is always guaranteed by SSGS.
Optimiser makes use of multithreading - up to 4 threads min(4, cpu_count)

## Results Summary

Full numbers are in `experiments/results_aggregate.csv` and `experiments/summary.md`. Averaged over 270 instances per dataset (excluding infeasible):

| Approach | J10 avg makespan | J20 avg makespan |
| -------- | ---------------: | ---------------: |
| Topological baseline (no optimisation) | 55.2 | 110.6 |
| SSGS with Activity ID priority | 40.7 | 69.8 |
| SSGS with LFT priority | 40.2 | 68.4 |
| GA + SSGS (28s) | 36.6 | 57.9 |
| ALNS + SSGS (28s) | 36.6 | 57.5 |

ALNS is our best performer on J20. J10 converges to 36.6 regardless of approach, which looks like the SSGS ceiling for those instances.

Infeasible counts: 17 out of 270 in J10, 4 out of 270 in J20. These are instances where an activity demands more of some resource than the total capacity. We detect these upfront and print `-1`.

## Notes

- Standard library only, as required.
- No external files are read at runtime other than the `.SCH` file passed in.
- The report PDF and slides are submitted separately.
