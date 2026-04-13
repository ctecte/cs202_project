"""
PERSON 5: Main entry point + integration
==========================================
ties everything together — parse the file, run the optimizer,
validate the result, print the schedule.

usage:
  python main.py <path_to_sch_file>
  python main.py ../sm_j10/PSP1.SCH
  python main.py --batch ../sm_j10/          (run all instances in folder)
"""

import sys
import os
import time

# make sure we can import from the same folder
sys.path.insert(0, os.path.dirname(__file__))

from parser import parse
from scheduler import ssgs, get_makespan, order_by_id, order_by_lft
from optimizer import genetic_algorithm
from validator import validate, compute_makespan, test_all_instances


TIME_BUDGET = 30  # seconds hard deadline
SAFETY_MARGIN = 5  # seconds safety buffer before deadline


def solve(filepath):
    """
    full pipeline: parse -> baseline heuristic -> GA optimization -> return best schedule.
    MUST return valid schedule before TIME_BUDGET expires.
    Balanced mode: order_by_id baseline + GA (0.5-1s) = ~0.1-0.2s total per instance.
    """
    global_start = time.time()
    project = parse(filepath)

    # --- STEP 1: Get baseline with order_by_id ---
    baseline_order = order_by_id(project)
    best_schedule = ssgs(project, baseline_order)
    best_makespan = get_makespan(project, best_schedule)

    # --- STEP 2: GA optimization (0.5-1s for meaningful improvement) ---
    elapsed = time.time() - global_start
    time_remaining = TIME_BUDGET - elapsed - SAFETY_MARGIN

    if time_remaining > 0.5:  # only run GA if we have at least 0.5s
        # Allocate 0.5-1s for GA
        time_for_ga = min(time_remaining - 1.0, 1.0)  # leave 1s buffer

        optimized = genetic_algorithm(project, time_limit=time_for_ga)
        if optimized:
            opt_makespan = get_makespan(project, optimized)
            if opt_makespan < best_makespan:
                best_schedule = optimized
                best_makespan = opt_makespan

    return project, best_schedule


def print_schedule(project, schedule):
    """pretty print the schedule."""
    print(f"\n{'='*50}")
    print(f"{'Activity':<12} {'Start':<8} {'Duration':<10} {'Finish':<8}")
    print(f"{'='*50}")

    for act_id in project.all_ids():
        act = project.activities[act_id]
        start = schedule[act_id]
        finish = start + act.duration
        label = f"activity {act_id}"
        if act_id == 0:
            label += " (start)"
        elif act_id == project.n + 1:
            label += " (end)"
        print(f"{label:<12} {start:<8} {act.duration:<10} {finish:<8}")

    makespan = compute_makespan(project, schedule)
    print(f"{'='*50}")
    print(f"Makespan: {makespan}")


def main():
    if len(sys.argv) < 2:
        print("usage: python main.py <file.SCH>")
        print("       python main.py --batch <folder>")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        # batch mode — run all instances in a folder
        folder = sys.argv[2] if len(sys.argv) > 2 else "../sm_j10"
        test_all_instances(folder, solve)
    else:
        # single instance mode
        filepath = sys.argv[1]
        start = time.time()

        project, schedule = solve(filepath)
        elapsed = time.time() - start

        # validate
        valid, violations = validate(project, schedule)

        # print results
        print_schedule(project, schedule)
        print(f"\nvalid: {valid}")
        if not valid:
            for v in violations[:10]:  # only show first 10
                print(f"  {v}")
        print(f"time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
