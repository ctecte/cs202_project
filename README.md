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

Per the submission guidelines, the grader runs our solver like this:

```
python src/main.py <path_to_sch_file>
```

Example:
```
python src/main.py sm_j10/PSP1.SCH
```

The program reads one `.SCH` instance file and prints the start times of activities 1 through N to stdout, comma separated. If the instance is infeasible (eg. some activity needs more of a resource than the total capacity), it prints `-1`.

Output matches the format from the project guidelines, eg:
```
0, 0, 0, 6, 1, 4, 9, 9, 18, 20
```

Everything else (makespan, validity, timing info) is sent to stderr so it does not interfere with the grader.

## Requirements

- Python 3.8 or later (we used 3.12)
- Standard library only, no external optimisation libraries like OR-Tools or Gurobi
- Runs within the 30 second time limit per instance

No `pip install` needed for the solver itself.

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
results_aggregate.csv   raw benchmark numbers from our experiments
summary.md        formatted summary of experiment runs
```

## Optional Flags

These are not part of the grader command but useful for us during development:

```
python src/main.py <file.SCH> --approach <ga|alns|lft_ssgs|id_ssgs|topo_seq>
python src/main.py <file.SCH> --time-budget <seconds>
python src/main.py <file.SCH> --workers <num_workers>
python src/main.py --batch <folder>
```

Default is `--approach ga` with a 28 second time budget (2 second safety margin from the 30s hard limit).

## How It Works (Short Version)

Full details are in the report. Quick summary:

1. **Parse** the `.SCH` file into a Project object holding activities, precedence dicts, and resource capacities.
2. **Feasibility check**: if any single activity demands more of a resource than the total capacity, output `-1` immediately.
3. **Baseline**: run SSGS with the LFT priority rule to get a guaranteed valid schedule.
4. **Optimise**: run either GA or ALNS for the rest of the time budget, trying thousands of different activity orderings. Each ordering is fed to SSGS which produces a schedule. Keep the best makespan found.

SSGS (Serial Schedule Generation Scheme) is the core. Given any precedence-feasible activity list, it walks through the list and places each activity at the earliest time where all predecessors are done and resources are free. It always produces a valid schedule.

The optimisers (GA and ALNS) only generate different activity lists. They never touch the schedule directly, so validity is always guaranteed by SSGS.

## Results Summary

Full numbers are in `results_aggregate.csv` and `summary.md`. Averaged over 270 instances per dataset (excluding infeasible):

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
