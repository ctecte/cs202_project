# CS202 Project: Resource-Constrained Project Scheduling (RCPSP)

## Problem Summary

You are given a project made up of **n activities** that need to be scheduled. Each activity has a duration and requires certain amounts of shared resources. Some activities must happen before others (precedence constraints), and the total resource usage at any point in time cannot exceed fixed capacities. The goal is to **minimize the total project completion time (makespan)**.

---

## Formal Definition

### Activities

- **n real activities**, numbered `1` to `n`
- **2 dummy activities**: activity `0` (project start) and activity `n+1` (project end), both with zero duration and zero resource usage

### Precedence Constraints

- A set of directed edges forming a **DAG** (Directed Acyclic Graph)
- If there is an edge `i -> j`, then activity `j` cannot start until activity `i` has **completely finished**
- Formally: `S_j >= S_i + d_i`

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
| `[lag_1], [lag_2], ...` | Time lags in brackets (can be ignored for basic RCPSP; the key info is which activities are successors) |

**Example:** Line `1  1  4  9  7  8  10  [9]  [1]  [8]  [2]` means:
- Activity `1` has **4 successors**: activities `9`, `7`, `8`, `10`
- This means: `1 -> 9`, `1 -> 7`, `1 -> 8`, `1 -> 10` (activity 1 must finish before any of these can start)

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

### Precedence Graph (DAG)

```
Activity 0 (start) -> 4, 2, 1, 3
Activity 1             -> 9, 7, 8, 10
Activity 2             -> 8
Activity 3             -> 10, 7
Activity 4             -> 10, 9, 5
Activity 5             -> 6
Activity 6             -> 11
Activity 7             -> 11
Activity 8             -> 1, 2, 11
Activity 9             -> 11
Activity 10            -> 11
Activity 11 (end)      -> (none)
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
Activity  0: Start =  0  (duration 0, finishes at  0)
Activity  1: Start =  0  (duration 3, finishes at  3)
Activity  2: Start =  3  (duration 10, finishes at 13)
Activity  3: Start =  0  (duration 3, finishes at  3)
Activity  4: Start =  0  (duration 3, finishes at  3)
Activity  5: Start =  3  (duration 3, finishes at  6)
Activity  6: Start =  6  (duration 5, finishes at 11)
Activity  7: Start =  3  (duration 10, finishes at 13)
Activity  8: Start = 13  (duration 2, finishes at 15)
Activity  9: Start =  3  (duration 6, finishes at  9)
Activity 10: Start =  3  (duration 1, finishes at  4)
Activity 11: Start = 15  (duration 0, finishes at 15)

Makespan (C_max) = 15
```

### Verifying the Schedule

**Precedence check** (every successor starts after its predecessor finishes):
- `0 -> 1`: S_1=0 >= S_0+d_0 = 0+0 = 0 ✓
- `0 -> 2`: S_2=3 >= 0+0 = 0 ✓
- `1 -> 7`: S_7=3 >= S_1+d_1 = 0+3 = 3 ✓
- `1 -> 8`: S_8=13 >= 0+3 = 3 ✓
- `2 -> 8`: S_8=13 >= S_2+d_2 = 3+10 = 13 ✓
- ... (and so on for every edge in the DAG)

**Resource check at time t=0** (activities running: 1, 3, 4):
- R1: 4+4+0 = 8 > 5 **VIOLATION** — this example would actually be infeasible at t=0!

This illustrates why you cannot simply start everything as early as possible based only on precedence. **Resource conflicts force you to delay some activities**, which is what makes this problem hard.

A **corrected valid schedule** might look like:

```
Activity  0: Start =  0
Activity  1: Start =  0  (uses R1=4)
Activity  2: Start =  3
Activity  3: Start =  3  (delayed to avoid R1 conflict with activity 1)
Activity  4: Start =  0  (uses R4=3, no conflict with activity 1)
Activity  5: Start =  6
Activity  6: Start =  9
Activity  7: Start =  6
Activity  8: Start = 16
Activity  9: Start =  6
Activity 10: Start =  6
Activity 11: Start = 18

Makespan (C_max) = 18
```

The goal is to find the schedule with the **smallest possible makespan** while respecting both precedence and resource constraints.

---

## Summary of What to Build

1. **Parser**: Read `.SCH` files and extract the activity data, precedence DAG, and resource capacities
2. **Scheduler**: Assign start times to all activities such that precedence and resource constraints are satisfied
3. **Optimizer**: Minimize the makespan — use heuristics and/or metaheuristics since the problem is NP-hard
4. **Time management**: Produce a valid (ideally good) solution within 30 seconds per instance
