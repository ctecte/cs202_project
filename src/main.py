"""
Main entry point: parse -> optimize -> output schedule.

Usage:
  python main.py <file.SCH>                  # single instance, prints comma-separated start times
  python main.py --batch <folder>            # batch test all instances in folder
  python main.py --batch <folder> --time 0.2 # batch with custom time limit per instance
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from parser import parse
from scheduler import ssgs, get_makespan, order_by_id, get_all_priority_orders, check_feasibility
from optimizer import optimize
from validator import validate, compute_makespan, test_all_instances


TIME_BUDGET = 28  # seconds — 2s buffer from the 30s limit


def solve(filepath, time_limit=TIME_BUDGET):
    """
    Full pipeline: parse -> check feasibility -> optimize -> return (project, best_schedule).
    Returns (project, schedule) where schedule is None if infeasible.
    """
    project = parse(filepath)

    # Check if any single activity exceeds resource capacity
    if not check_feasibility(project):
        return project, None

    # Quick baseline with best priority rule
    best_schedule = None
    best_makespan = float('inf')

    for name, order in get_all_priority_orders(project):
        sched = ssgs(project, order)
        if sched is None:
            continue
        ms = get_makespan(project, sched)
        if ms < best_makespan:
            best_makespan = ms
            best_schedule = sched

    # Run optimizer to improve
    if time_limit > 0.5 and best_schedule is not None:
        opt_sched, opt_ms = optimize(project, time_limit=time_limit - 0.1)
        if opt_sched and opt_ms < best_makespan:
            best_schedule = opt_sched
            best_makespan = opt_ms

    return project, best_schedule


def format_output(project, schedule):
    """Format as comma-separated start times for activities 1..N."""
    if schedule is None:
        return "-1"
    start_times = []
    for act_id in range(1, project.n + 1):
        start_times.append(str(schedule[act_id]))
    return ", ".join(start_times)


def main():
    if len(sys.argv) < 2:
        print("usage: python main.py <file.SCH>")
        print("       python main.py --batch <folder> [--time <seconds>]")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        # Batch mode
        folder = sys.argv[2] if len(sys.argv) > 2 else "../sm_j10"
        per_time = 0.2
        if "--time" in sys.argv:
            idx = sys.argv.index("--time")
            per_time = float(sys.argv[idx + 1])

        def batch_solver(filepath):
            return solve(filepath, time_limit=per_time)

        test_all_instances(folder, batch_solver)
    else:
        # Single instance mode
        filepath = sys.argv[1]
        start = time.time()

        project, schedule = solve(filepath, time_limit=TIME_BUDGET)
        elapsed = time.time() - start

        # Output format: comma-separated start times or -1
        print(format_output(project, schedule))

        # Validation info to stderr
        if schedule is not None:
            valid, violations = validate(project, schedule)
            makespan = compute_makespan(project, schedule)
            sys.stderr.write(f"makespan={makespan} valid={valid} time={elapsed:.2f}s\n")
            if not valid:
                for v in violations[:5]:
                    sys.stderr.write(f"  {v}\n")
        else:
            sys.stderr.write(f"infeasible time={elapsed:.2f}s\n")


if __name__ == "__main__":
    main()
