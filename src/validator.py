# validator: checks if a schedule is actually valid
# two things to check: precedence constraints and resource constraints at every time step
# also handles batch testing across all instances

import os
import sys
import re
from models import Project


def check_precedence(project, schedule):
    # for every edge i->j, check that S_j >= S_i + d_i
    # returns list of violation strings, empty means all good
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
    # at every time step, sum up resource usage across all running activities
    # check that none exceed capacity
    # returns list of violation strings, empty means all good
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
    # run precedence and resource checks, returns (is_valid, list of violations)
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
    # makespan = start time of the dummy end activity
    end_id = project.n + 1
    return schedule.get(end_id, -1)


# ========================================
# BATCH TESTING
# ========================================

def test_all_instances(folder, solver_fn):
    # run solver on every .SCH file in the folder
    # prints makespan, valid/invalid, time taken per instance
    # prints aggregate stats at the end
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
