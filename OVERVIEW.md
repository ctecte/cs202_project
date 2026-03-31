# CS202 Project: Resource-Constrained Project Scheduling (RCPSP)

## Problem Summary

You are given a project made up of **n activities** that need to be scheduled. Each activity has a duration and requires certain amounts of shared resources. Some activities must happen before others (precedence constraints), and the total resource usage at any point in time cannot exceed fixed capacities. The goal is to **minimize the total project completion time (makespan)**.

---

## Formal Definition

### Activities

- **n real activities**, numbered `1` to `n`
- **2 dummy activities**: activity `0` (project start) and activity `n+1` (project end), both with zero duration and zero resource usage

### Precedence Constraints (Time Lags)

- The data file lists **temporal relations** between activities, each with a **lag value `L`**
- For an edge `i -> j` with lag `L`, the constraint is: `S_j >= S_i + L`
- **Negative lags** (`L < 0`): not real dependencies — skip these edges entirely (they are always satisfied)
- **Non-negative lags** (`L >= 0`): real constraints that must be enforced
- Note: the lag `L` is **not the same as the duration** `d_i`. The lag comes from the brackets in the successor table; the duration comes from the resource table. They are independent values.

### Resources

- **K renewable resource types** (e.g., workers, cranes, machines)
- Each resource type `k` has a fixed capacity `R_k` (available at every time step)
- Each activity `i` requires `r_{i,k}` units of resource `k` for its **entire duration**
- At every time `t`: the sum of `r_{i,k}` over all activities running at time `t` must be `<= R_k`

### Objective

Find a start time `S_i` for each activity that:

1. Respects all precedence constraints
2. Never exceeds any resource capacity at any point in time
3. **Minimizes** `C_max = S_{n+1}` (the start time of the dummy end activity = project completion time)

---

## Constraints and Rules

- **30-second wall-clock time limit** per instance on the grading machine
- No external optimization/scheduling libraries (no OR-Tools, PuLP, Gurobi, CPLEX)
- Standard library data structures (heaps, queues, hash maps, etc.) are allowed
- Groups of up to 5 students
- Will be evaluated on **harder unseen instances**, so don't overfit to the provided benchmarks

---

## Dataset

Two benchmark sets from [PSPLIB](http://www.om-db.wi.tum.de/psplib/), in the `ProGenMax` format:

| Folder    | Activities per instance | Number of instances |
|-----------|------------------------|---------------------|
| `sm_j10/` | 10 (+ 2 dummies = 12 total) | 270 `.SCH` files |
| `sm_j20/` | 20 (+ 2 dummies = 22 total) | 270 `.SCH` files |

Each folder also contains a `PARAMS.TXT` file describing the generation parameters (not needed for solving).

---

## Input File Format (`.SCH` files)

Each `.SCH` file has three sections. Here is `PSP1.SCH` from `sm_j10/` as a worked example:

### Raw File Content

```
10	5	0	0
0	1	4	4	2	1	3	[0]	[0]	[0]	[0]
1	1	4	9	7	8	10	[9]	[1]	[8]	[2]
2	1	1	8	[24]
3	1	2	10	7	[4]	[8]
4	1	3	10	9	5	[0]	[0]	[7]
5	1	1	6	[0]
6	1	1	11	[5]
7	1	1	11	[10]
8	1	3	1	2	11	[-22]	[-34]	[2]
9	1	1	11	[6]
10	1	1	11	[1]
11	1	0
0	1	0	0	0	0	0	0
1	1	3	4	1	0	0	0
2	1	10	1	0	3	0	0
3	1	3	4	0	2	2	3
4	1	3	0	0	0	3	0
5	1	3	0	1	2	4	0
6	1	5	2	3	4	0	0
7	1	10	0	4	4	0	4
8	1	2	2	0	0	4	4
9	1	6	5	0	0	1	1
10	1	1	0	1	0	0	0
11	1	0	0	0	0	0	0
5	5	5	5	5
```

### Section 1: Header (Line 1)

```
10  5  0  0
```

| Field | Meaning |
|-------|---------|
| `10`  | Number of real activities (`n`) |
| `5`   | Number of resource types (`K`) |
| `0 0` | Unused (can be ignored) |

Total activities including dummies: `n + 2 = 12` (numbered `0` to `11`)

### Section 2: Precedence / Successors (Lines 2 to n+3)

One line per activity, from activity `0` to activity `n+1`:

```
activity_id  1  num_successors  succ_1  succ_2  ...  [lag_1]  [lag_2]  ...
```

| Field | Meaning |
|-------|---------|
| `activity_id` | The activity number |
| `1` | Number of modes (always 1 for single-mode RCPSP) |
| `num_successors` | How many activities directly follow this one |
| `succ_1, succ_2, ...` | The IDs of successor activities |
| `[lag_1], [lag_2], ...` | Time lags in brackets — each lag pairs with the corresponding successor. **These matter.** |

**Example:** Line `1  1  4  9  7  8  10  [9]  [1]  [8]  [2]` means:
- Activity `1` has **4 successors**: activities `9`, `7`, `8`, `10`
- With lags: `1 -> 9` (lag 9), `1 -> 7` (lag 1), `1 -> 8` (lag 8), `1 -> 10` (lag 2)
- Constraints: `S_9 >= S_1 + 9`, `S_7 >= S_1 + 1`, `S_8 >= S_1 + 8`, `S_10 >= S_1 + 2`

**Negative lags:** Line `8  1  3  1  2  11  [-22]  [-34]  [2]` means:
- Activity `8` has 3 successors: `1`, `2`, `11` with lags `-22`, `-34`, `2`
- `8 -> 1` (lag -22): **skip** — negative lag, not a real dependency
- `8 -> 2` (lag -34): **skip** — negative lag
- `8 -> 11` (lag 2): **enforce** `S_11 >= S_8 + 2`

The last activity (`11`) has `0` successors (it is the dummy end node).

### Section 3: Durations and Resource Requirements (Lines n+4 to 2n+5)

One line per activity, from activity `0` to activity `n+1`:

```
activity_id  1  duration  r_1  r_2  r_3  ...  r_K
```

| Field | Meaning |
|-------|---------|
| `activity_id` | The activity number |
| `1` | Mode (always 1) |
| `duration` | How many time units the activity takes |
| `r_1 ... r_K` | Units of each resource required during the entire execution |

**Example:** `7  1  10  0  4  4  0  4` means:
- Activity `7` has duration **10**
- Requires: 0 of R1, 4 of R2, 4 of R3, 0 of R4, 4 of R5

### Section 4: Resource Capacities (Last Line)

```
5  5  5  5  5
```

The maximum available units for each resource type. Here all 5 resources have a capacity of 5.

---

## Parsed Example: PSP1.SCH (J10)

### Precedence Graph (only edges with non-negative lags)

```
Activity 0 (start) -> 4 [0], 2 [0], 1 [0], 3 [0]
Activity 1         -> 9 [9], 7 [1], 8 [8], 10 [2]
Activity 2         -> 8 [24]
Activity 3         -> 10 [4], 7 [8]
Activity 4         -> 10 [0], 9 [0], 5 [7]
Activity 5         -> 6 [0]
Activity 6         -> 11 [5]
Activity 7         -> 11 [10]
Activity 8         -> 11 [2]          (edges to 1 and 2 skipped: negative lags)
Activity 9         -> 11 [6]
Activity 10        -> 11 [1]
Activity 11 (end)  -> (none)
```

### Activity Table

| Activity | Duration | R1 | R2 | R3 | R4 | R5 |
|----------|----------|----|----|----|----|----|
| 0 (start)| 0        | 0  | 0  | 0  | 0  | 0  |
| 1        | 3        | 4  | 1  | 0  | 0  | 0  |
| 2        | 10       | 1  | 0  | 3  | 0  | 0  |
| 3        | 3        | 4  | 0  | 2  | 2  | 3  |
| 4        | 3        | 0  | 0  | 0  | 3  | 0  |
| 5        | 3        | 0  | 1  | 2  | 4  | 0  |
| 6        | 5        | 2  | 3  | 4  | 0  | 0  |
| 7        | 10       | 0  | 4  | 4  | 0  | 4  |
| 8        | 2        | 2  | 0  | 0  | 4  | 4  |
| 9        | 6        | 5  | 0  | 0  | 1  | 1  |
| 10       | 1        | 0  | 1  | 0  | 0  | 0  |
| 11 (end) | 0        | 0  | 0  | 0  | 0  | 0  |

**Resource capacities:** R1=5, R2=5, R3=5, R4=5, R5=5

---

## Expected Output

Your program should output the **start time** for each activity. A valid schedule for the above example:

```
Activity  0: Start =  0  (duration  0, finishes at  0)
Activity  1: Start =  0  (duration  3, finishes at  3)
Activity  2: Start =  0  (duration 10, finishes at 10)
Activity  3: Start =  3  (duration  3, finishes at  6)
Activity  4: Start =  0  (duration  3, finishes at  3)
Activity  5: Start =  7  (duration  3, finishes at 10)
Activity  6: Start = 10  (duration  5, finishes at 15)
Activity  7: Start =  8  (duration 10, finishes at 18)
Activity  8: Start = 24  (duration  2, finishes at 26)
Activity  9: Start =  9  (duration  6, finishes at 15)
Activity 10: Start =  4  (duration  1, finishes at  5)
Activity 11: Start = 26  (duration  0, finishes at 26)

Makespan (C_max) = 26
```

### Verifying the Schedule

**Precedence check** (for every edge `i -> j` with lag `L >= 0`, verify `S_j >= S_i + L`):
- `0 -> 1` (lag 0): S_1=0 >= S_0 + 0 = 0 ✓
- `0 -> 4` (lag 0): S_4=0 >= S_0 + 0 = 0 ✓
- `1 -> 9` (lag 9): S_9=9 >= S_1 + 9 = 0+9 = 9 ✓
- `1 -> 8` (lag 8): S_8=24 >= S_1 + 8 = 0+8 = 8 ✓
- `2 -> 8` (lag 24): S_8=24 >= S_2 + 24 = 0+24 = 24 ✓
- ... (and so on for every edge with non-negative lag)

**Resource check at each time step** — at every time `t`, sum up resource usage from all running activities and verify it doesn't exceed capacity.

The goal is to find the schedule with the **smallest possible makespan** while respecting both precedence (lag) and resource constraints.

---

## Summary of What to Build

1. **Parser**: Read `.SCH` files and extract the activity data, precedence DAG, and resource capacities
2. **Scheduler**: Assign start times to all activities such that precedence and resource constraints are satisfied
3. **Optimizer**: Minimize the makespan — use heuristics and/or metaheuristics since the problem is NP-hard
4. **Time management**: Produce a valid (ideally good) solution within 30 seconds per instance
