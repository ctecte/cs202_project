"""
Validator: checks schedule correctness (precedence + resources).
Also handles batch testing.
"""

import os
import time
from models import Project


def check_precedence(project, schedule):
    """
    For each edge i -> j: S_j must be >= S_i + d_i.
    Returns list of violation strings (empty = valid).
    """
    violations = []
    for act_id in project.all_ids():
        act = project.activities[act_id]
        for succ_id in project.successors[act_id]:
            if schedule[succ_id] < schedule[act_id] + act.duration:
                violations.append(
                    f"PRECEDENCE: {act_id}->{succ_id}, "
                    f"S_{succ_id}={schedule[succ_id]} < S_{act_id}+d_{act_id}={schedule[act_id]+act.duration}"
                )
    return violations


def check_resources(project, schedule):
    """
    At every time step t, total resource usage must not exceed capacity.
    Returns list of violation strings (empty = valid).
    """
    violations = []

    # Build time -> resource usage map
    max_time = 0
    for act_id in project.all_ids():
        s = schedule[act_id]
        d = project.activities[act_id].duration
        if s + d > max_time:
            max_time = s + d

    for t in range(max_time):
        usage = [0] * project.k
        for act_id in project.all_ids():
            s = schedule[act_id]
            d = project.activities[act_id].duration
            if d > 0 and s <= t < s + d:
                for r in range(project.k):
                    usage[r] += project.activities[act_id].resources[r]

        for r in range(project.k):
            if usage[r] > project.capacities[r]:
                violations.append(
                    f"RESOURCE: t={t}, R{r+1}: usage {usage[r]} > cap {project.capacities[r]}"
                )
    return violations


def validate(project, schedule):
    """Run all checks. Returns (is_valid, list_of_violations)."""
    violations = []

    # sanity: every activity must have a start time
    for act_id in project.all_ids():
        if act_id not in schedule:
            violations.append(f"MISSING: activity {act_id} has no start time")

    if violations:
        return False, violations

    violations += check_precedence(project, schedule)
    violations += check_resources(project, schedule)

    return len(violations) == 0, violations


def compute_makespan(project, schedule):
    """Makespan = start time of dummy end activity."""
    return schedule.get(project.n + 1, -1)


def test_all_instances(folder, solver_fn, time_limit_per=0.2):
    """
    Run solver on every .SCH file in folder, validate, report results.
    time_limit_per: max seconds per instance (for testing, not the real 30s budget).
    """
    from parser import parse

    sch_files = sorted([f for f in os.listdir(folder) if f.upper().endswith('.SCH')])
    print(f"Found {len(sch_files)} instances in {folder}")

    num_valid = 0
    num_invalid = 0
    num_error = 0
    total_makespan = 0
    makespans = []

    for filename in sch_files:
        filepath = os.path.join(folder, filename)
        start = time.time()

        try:
            project, schedule = solver_fn(filepath)
            elapsed = time.time() - start

            valid, violations = validate(project, schedule)
            makespan = compute_makespan(project, schedule)

            if valid:
                num_valid += 1
                total_makespan += makespan
                makespans.append(makespan)
            else:
                num_invalid += 1
                print(f"  INVALID {filename}: {violations[:3]}")

        except Exception as e:
            num_error += 1
            print(f"  ERROR {filename}: {e}")

    total = len(sch_files)
    print(f"\n{'='*50}")
    print(f"Valid: {num_valid}/{total}  Invalid: {num_invalid}  Errors: {num_error}")
    if num_valid > 0:
        print(f"Avg makespan: {total_makespan / num_valid:.1f}")
        print(f"Min: {min(makespans)}  Max: {max(makespans)}")
    print(f"{'='*50}")
