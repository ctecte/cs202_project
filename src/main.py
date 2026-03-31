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
from scheduler import ssgs, get_makespan, order_by_id
from optimizer import genetic_algorithm
from validator import validate, compute_makespan, test_all_instances


TIME_BUDGET = 28  # seconds — leave 2s buffer from the 30s limit


def solve(filepath):
    """
    full pipeline: parse -> optimize -> return best schedule.
    this is what gets called for each instance.
    """
    project = parse(filepath)

    # --- STRATEGY ---
    # step 1: get a quick baseline with a simple priority rule
    # (this gives us a valid schedule immediately, even if the optimizer
    #  hasn't been implemented yet)
    baseline_order = order_by_id(project)
    best_schedule = ssgs(project, baseline_order)
    best_makespan = get_makespan(project, best_schedule)

    # step 2: try to improve with the optimizer
    # TODO: uncomment this once optimizer is implemented
    # optimized = genetic_algorithm(project, time_limit=TIME_BUDGET)
    # if optimized:
    #     opt_makespan = get_makespan(project, optimized)
    #     if opt_makespan < best_makespan:
    #         best_schedule = optimized
    #         best_makespan = opt_makespan

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
