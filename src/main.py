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
import random
import multiprocessing as mp

# make sure we can import from the same folder
sys.path.insert(0, os.path.dirname(__file__))

from parser import parse
from scheduler import ssgs, get_makespan, order_by_id, order_by_lft
from optimizer import genetic_algorithm
from validator import validate, compute_makespan, test_all_instances


TIME_BUDGET = 28  # seconds — leave 2s buffer from the 30s limit
DEFAULT_WORKERS = max(1, mp.cpu_count())


def _extract_workers(argv):
    """Read optional --workers N from argv, fallback to default on invalid input."""
    if "--workers" not in argv:
        return DEFAULT_WORKERS
    idx = argv.index("--workers")
    if idx + 1 >= len(argv):
        return DEFAULT_WORKERS
    try:
        return max(1, int(argv[idx + 1]))
    except ValueError:
        return DEFAULT_WORKERS


def _extract_time_budget(argv):
    """Read optional --time-budget seconds from argv."""
    if "--time-budget" not in argv:
        return TIME_BUDGET
    idx = argv.index("--time-budget")
    if idx + 1 >= len(argv):
        return TIME_BUDGET
    try:
        return max(0.1, float(argv[idx + 1]))
    except ValueError:
        return TIME_BUDGET


def _worker_optimize(task):
    """Independent portfolio worker with its own random seed."""
    filepath, seed, time_budget = task
    random.seed(seed)

    project = parse(filepath)
    schedule = genetic_algorithm(project, time_limit=time_budget)
    makespan = get_makespan(project, schedule)
    return makespan, schedule


def solve(filepath, workers=1, time_budget=TIME_BUDGET):
    """
    full pipeline: parse -> optimize -> return best schedule.
    this is what gets called for each instance.
    """
    project = parse(filepath)

    # --- STRATEGY ---
    # step 1: get a quick baseline with a simple priority rule
    # (this gives us a valid schedule immediately, even if the optimizer
    #  hasn't been implemented yet)
    baseline_order = order_by_lft(project)
    best_schedule = ssgs(project, baseline_order)
    best_makespan = get_makespan(project, best_schedule)

    # step 2: try to improve with the optimizer
    if workers <= 1:
        try:
            optimized = genetic_algorithm(project, time_limit=time_budget)
            if optimized:
                opt_makespan = get_makespan(project, optimized)
                if opt_makespan < best_makespan:
                    best_schedule = optimized
                    best_makespan = opt_makespan
        except Exception:
            # Keep baseline schedule on optimizer failure to preserve CLI behavior.
            pass
    else:
        # Portfolio restarts: multiple random seeds in parallel, keep the best result.
        base_seed = int(time.time() * 1000) % 1_000_000_007
        tasks = [(filepath, base_seed + i * 9973, time_budget) for i in range(workers)]
        try:
            ctx = mp.get_context("spawn")
            with ctx.Pool(processes=workers) as pool:
                for opt_makespan, optimized in pool.imap_unordered(_worker_optimize, tasks):
                    if optimized and opt_makespan < best_makespan:
                        best_schedule = optimized
                        best_makespan = opt_makespan
        except Exception as e:
            print(
                f"[warn] multiprocessing portfolio failed on {os.path.basename(filepath)}: {e}; falling back to single worker",
                file=sys.stderr,
            )
            # Fallback if multiprocessing fails in current environment.
            try:
                optimized = genetic_algorithm(project, time_limit=time_budget)
                if optimized:
                    opt_makespan = get_makespan(project, optimized)
                    if opt_makespan < best_makespan:
                        best_schedule = optimized
                        best_makespan = opt_makespan
            except Exception:
                pass

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
        print("optional: --workers <num_workers>")
        print("optional: --time-budget <seconds_per_instance>")
        sys.exit(1)

    workers = _extract_workers(sys.argv)
    time_budget = _extract_time_budget(sys.argv)

    if sys.argv[1] == "--batch":
        # batch mode — run all instances in a folder
        folder = sys.argv[2] if len(sys.argv) > 2 else "../sm_j10"
        print(f"batch config: workers={workers}, time_budget={time_budget:.2f}s", file=sys.stderr)
        test_all_instances(folder, lambda fp: solve(fp, workers=workers, time_budget=time_budget))
    else:
        # single instance mode
        filepath = sys.argv[1]
        start = time.time()

        project, schedule = solve(filepath, workers=workers, time_budget=time_budget)
        elapsed = time.time() - start

        # validate
        valid, violations = validate(project, schedule)

        # print results
        print_schedule(project, schedule)
        print(f"\nvalid: {valid}")
        if not valid:
            for v in violations[:10]:  # only show first 10
                print(f"  {v}")
        print(f"workers: {workers}")
        print(f"time_budget: {time_budget:.2f}s")
        print(f"time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
