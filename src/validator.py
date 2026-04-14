"""
PERSON 4: Validator & Testing
==============================
this module checks if a schedule is actually valid — no cheating lah.

two things to verify:
  1. precedence: for every edge i->j, S_j >= S_i + d_i
  2. resources: at every time step t, total resource usage <= capacity

also handles batch testing across all instances.
"""

import os
import sys
import re
from models import Project


def check_precedence(project, schedule):
    """
    check all precedence constraints.
    for each edge i -> j:
        S_j must be >= S_i + d_i

    returns a list of violation strings. empty list = all good.
    """
    violations = []

    for act_id in project.all_ids():
        act = project.activities[act_id]
        for succ_id in project.successors[act_id]:
            if schedule[succ_id] < schedule[act_id] + act.duration:
                violations.append(
                    f"PRECEDENCE FAIL: activity {act_id} -> {succ_id}, "
                    f"S_{succ_id}={schedule[succ_id]} < S_{act_id}+d_{act_id}={schedule[act_id]+act.duration}"
                )

    return violations


def check_resources(project, schedule):
    """
    check resource constraints at every time step.

    approach:
      1. figure out which activities are running at each time step
         (activity i runs during [S_i, S_i + d_i))
      2. sum up resource usage at each time step
      3. check against capacity

    returns a list of violation strings. empty list = all good.
    """
    violations = []

    max_time = max(schedule[i] + project.activities[i].duration for i in project.all_ids())

    for t in range(max_time):
        usage = [0] * project.k
        for act_id in project.all_ids():
            s = schedule[act_id]
            d = project.activities[act_id].duration
            if s <= t < s + d:
                for r in range(project.k):
                    usage[r] += project.activities[act_id].resources[r]

        for r in range(project.k):
            if usage[r] > project.capacities[r]:
                violations.append(
                    f"RESOURCE FAIL: time {t}, resource R{r+1}: "
                    f"usage {usage[r]} > capacity {project.capacities[r]}"
                )

    return violations


def validate(project, schedule):
    """
    run all checks on a schedule. returns (is_valid, list_of_violations).
    """
    violations = []

    # basic sanity check — make sure every activity has a start time
    for act_id in project.all_ids():
        if act_id not in schedule:
            violations.append(f"MISSING: activity {act_id} has no start time")

    if violations:
        return False, violations

    # check constraints
    violations += check_precedence(project, schedule)
    violations += check_resources(project, schedule)

    return len(violations) == 0, violations


def compute_makespan(project, schedule):
    """makespan = start time of the dummy end activity."""
    end_id = project.n + 1
    return schedule.get(end_id, -1)


# ========================================
# BATCH TESTING
# ========================================

def test_all_instances(folder, solver_fn):
    """
    run the solver on every .SCH file in a folder and report results.

    solver_fn: a function that takes a filepath and returns a (project, schedule) tuple

    TODO: implement — this should:
      1. find all .SCH files in the folder
      2. for each file, run the solver
      3. validate the schedule
      4. print a summary (makespan, valid/invalid, time taken)
      5. at the end, print aggregate stats (avg makespan, num valid, etc.)
    """
    from parser import parse
    import time

    def natural_psp_key(name):
        stem = os.path.splitext(name)[0]
        m = re.search(r"([0-9]+)$", stem)
        if m:
            return (int(m.group(1)), name)
        return (10**9, name)

    sch_files = sorted([f for f in os.listdir(folder) if f.endswith('.SCH')], key=natural_psp_key)
    print(f"found {len(sch_files)} instances in {folder}")

    results = []
    num_valid = 0
    total_makespan = 0

    def render_progress(done, total, label):
        width = 28
        filled = int(width * done / max(1, total))
        bar = "#" * filled + "-" * (width - filled)
        pct = int(100 * done / max(1, total))
        print(f"\r[{bar}] {pct:3d}% ({done}/{total}) {label}", end="", file=sys.stderr, flush=True)

    total = len(sch_files)

    for idx, filename in enumerate(sch_files, start=1):
        filepath = os.path.join(folder, filename)

        start = time.time()
        try:
            project, schedule = solver_fn(filepath)
            elapsed = time.time() - start

            if schedule is None:
                results.append((filename, -1, elapsed, "INFEASIBLE"))
                print(f"  [{idx}/{total}] {filename}: INFEASIBLE, time={elapsed:.2f}s")
                render_progress(idx, total, filename)
                continue

            valid, violations = validate(project, schedule)
            makespan = compute_makespan(project, schedule)

            if valid:
                num_valid += 1
                total_makespan += makespan
                status = "OK"
            else:
                status = f"INVALID ({len(violations)} violations)"

            results.append((filename, makespan, elapsed, status))
            print(f"  [{idx}/{total}] {filename}: makespan={makespan}, time={elapsed:.2f}s, {status}")
            render_progress(idx, total, filename)

        except Exception as e:
            elapsed = time.time() - start
            results.append((filename, -1, elapsed, f"ERROR: {e}"))
            print(f"  [{idx}/{total}] {filename}: ERROR — {e}")
            render_progress(idx, total, filename)

    print(file=sys.stderr)

    print(f"\n{'='*50}")
    print(f"valid: {num_valid}/{len(sch_files)}")
    if num_valid > 0:
        print(f"avg makespan (valid only): {total_makespan / num_valid:.1f}")
    print(f"{'='*50}")

    return results


# quick test
if __name__ == "__main__":
    from parser import parse
    from scheduler import ssgs, order_by_id

    path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP1.SCH")
    proj = parse(path)

    order = order_by_id(proj)
    sched = ssgs(proj, order)

    valid, violations = validate(proj, sched)
    print(f"valid: {valid}")
    if not valid:
        for v in violations:
            print(f"  {v}")
    print(f"makespan: {compute_makespan(proj, sched)}")
