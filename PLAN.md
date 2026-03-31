# Project Plan: RCPSP Solver

see OVERVIEW.md for the full problem description and data format.

## how the pieces fit together

```
  .SCH file
      |
      v
  [ parser.py ]  ──>  Project object
                          |
                          v
  [ optimizer.py ]  tries thousands of activity orderings
       |                   |
       |    for each ordering, calls...
       v                   v
  [ scheduler.py ]  ──>  Schedule (activity -> start time)
       |
       v
  [ validator.py ]  checks if the schedule is legit
       |
       v
  [ main.py ]  ties everything together, handles CLI
```

the optimizer generates many different activity orderings.
for each ordering, the scheduler (SSGS) builds a schedule.
we keep the best one (lowest makespan).

---

## roles

### person 1: parser (`parser.py`)

**what to do:**
parse .SCH files into the Project data structure that everyone else uses.
you're the first one to finish because everyone depends on your output.

**tasks:**
1. parse the header line (n and K)
2. parse the successor table — extract successor ids and lag values from brackets
3. filter out edges with negative lags (those aren't real dependencies)
4. build the successors dict AND predecessors dict (reverse the edges)
5. parse the duration/resource table into Activity objects
6. parse the last line for resource capacities
7. test on PSP1.SCH — print everything out and manually verify against OVERVIEW.md
8. test on ALL 270 j10 files to make sure nothing crashes

**things to watch out for:**
- the bracket values can be negative like [-22] — use regex or string ops to handle
- make sure predecessors dict is built correctly (reverse of successors)
- activities 0 and n+1 are dummies — they should have duration 0 and all-zero resources

**done when:** running `python parser.py` prints correct parsed output for PSP1.SCH.

---

### person 2: scheduler (`scheduler.py`)

**what to do:**
implement the Serial Schedule Generation Scheme (SSGS).
this is the core engine — given an ordering of activities, produce a valid schedule.

**tasks:**
1. implement `ResourceTracker.is_feasible()` — check if resources are available
2. implement `ResourceTracker.book()` — record resource usage
3. implement `find_earliest_start()` — find earliest time respecting both precedence and resources
4. implement `ssgs()` — the main scheduling loop
5. implement at least 2 priority rules: `order_by_id` (trivial), `order_by_lft` (good)
6. test with validator on j10 instances

**how SSGS works (pseudocode):**
```
schedule activity 0 at time 0
for each activity in the given order:
    earliest = max(S_pred + lag) over all predecessors
    while resources not available at earliest:
        earliest += 1
    schedule activity at earliest
schedule activity n+1 at earliest feasible time
```

**things to watch out for:**
- the activity list must be precedence-feasible (person 3 handles this)
- for resource checking, activity i occupies resources during [S_i, S_i + duration)
- ResourceTracker uses a dict keyed by time — don't preallocate a huge array

**done when:** `ssgs()` produces valid schedules (confirmed by validator) on all j10 instances.

---

### person 3: optimizer (`optimizer.py`)

**what to do:**
search for the best activity ordering using a metaheuristic.
you generate THOUSANDS of orderings, run each through SSGS, keep the best.

**tasks:**
1. implement `random_activity_list()` — random topological sort
2. implement `is_precedence_feasible()` — sanity check
3. pick GA or SA (or both), implement the main loop
4. for GA: implement crossover, mutation, tournament selection
5. for SA: implement neighbor generation, cooling schedule
6. tune parameters (population size, mutation rate, temperature, etc.)
7. benchmark on j10 and j20

**GA overview:**
```
generate 50 random activity lists (population)
evaluate each with SSGS → get makespan
while time left:
    pick 2 parents (tournament selection)
    crossover → child
    mutate child
    evaluate child with SSGS
    if better than worst in population, replace it
return best schedule found
```

**SA overview:**
```
start with 1 random activity list
while time left:
    swap two adjacent activities → neighbor
    if neighbor gives better makespan, keep it
    if worse, keep it with probability e^(-delta/temperature)
    cool down temperature
return best schedule found
```

**things to watch out for:**
- every activity list must be precedence-feasible — crossover can break this
- time management is crucial — check `time.time()` regularly, stop before 30s
- SA is simpler to implement but GA usually finds better solutions
- start with SA if GA crossover is too confusing

**done when:** optimizer finds better makespans than the baseline priority rules on most instances.

---

### person 4: validator + testing (`validator.py`)

**what to do:**
make sure our schedules are actually correct.
also build the testing infrastructure to run on all instances.

**tasks:**
1. implement `check_precedence()` — verify S_j >= S_i + L for all edges
2. implement `check_resources()` — verify resource usage <= capacity at every time step
3. implement `validate()` — combine both checks
4. implement `test_all_instances()` — batch test on a folder of .SCH files
5. create a summary report: how many valid, avg makespan, worst case, etc.
6. (bonus) compare against known optimal solutions from PSPLIB for j10

**things to watch out for:**
- resource check needs to iterate over every time step — can be slow for bad schedules
- activity runs during [S_i, S_i + d_i), not [S_i, S_i + d_i]
- edge case: activities with duration 0 don't use resources at any time step

**done when:** validator correctly catches invalid schedules AND passes valid ones.

---

### person 5: integration + analysis (`main.py`)

**what to do:**
glue everything together. handle CLI, time budget, output formatting.
also own the final benchmarking and report.

**tasks:**
1. implement `solve()` — the full pipeline (parse → optimize → return schedule)
2. implement CLI: single instance mode + batch mode
3. time management — make sure we stay under 30s per instance
4. run final benchmarks on j10 and j20
5. collect stats: avg/min/max makespan, computation time
6. write the analysis/report
7. make sure submission format is correct

**things to watch out for:**
- leave 2s buffer from the 30s limit (use 28s as the actual budget)
- fallback: if optimizer hasn't finished, return the baseline schedule
- the grading will use harder unseen instances — don't hardcode anything

**done when:** `python main.py --batch ../sm_j10/` runs all 270 instances, all valid, under 30s each.

---

## suggested timeline

| phase | who | what |
|-------|-----|------|
| phase 1 | person 1 | finish parser, share with team |
| phase 1 | person 4 | write validator (can test with dummy schedules first) |
| phase 2 | person 2 | implement SSGS + basic priority rule |
| phase 2 | person 5 | set up main.py, integrate parser |
| phase 3 | person 2 | add LFT priority rule |
| phase 3 | person 3 | implement optimizer (start with SA, then try GA) |
| phase 3 | person 4 | batch test SSGS baseline on all instances |
| phase 4 | person 3 | tune optimizer parameters |
| phase 4 | person 5 | final benchmarks + report |
| phase 4 | everyone | review, clean up, submit |

person 1 and 4 should be done earliest so the rest can build on top.
person 2 and 3 are the most algo-heavy roles.
person 5 keeps things glued and manages the final submission.
