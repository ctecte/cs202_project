# main entry point: parse the file, run the optimizer, print the schedule
# usage:
#   python main.py <path_to_sch_file>
#   python main.py --batch <folder>    (run all instances in folder)

import sys
import os
import time
import random
import multiprocessing as mp

# make sure we can import from the same folder
sys.path.insert(0, os.path.dirname(__file__))

from parser import parse
from scheduler import (
    ssgs,
    get_makespan,
    order_by_id,
    order_by_lft,
    topological_sequential_schedule,
    check_feasibility,
)
from optimizer import genetic_algorithm, alns_optimize
from validator import validate, compute_makespan, test_all_instances


TIME_BUDGET = 28  # seconds — leave 2s buffer from the 30s limit
DEFAULT_WORKERS = 4 if (mp.cpu_count() or 1) >= 4 else 1

APPROACH_LABELS = {
    "topo_seq": "Topological Sequential Baseline (precedence-only)",
    "id_ssgs": "SSGS with Activity-ID Priority",
    "lft_ssgs": "SSGS with Latest Finish Time Priority",
    "ga": "Genetic Algorithm + SSGS Decoder",
    "alns": "Adaptive Large Neighborhood Search + SSGS Decoder",
}


def _extract_workers(argv):
    # parse --workers N from argv, falls back to default if missing or invalid
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
    # parse --time-budget seconds from argv
    if "--time-budget" not in argv:
        return TIME_BUDGET
    idx = argv.index("--time-budget")
    if idx + 1 >= len(argv):
        return TIME_BUDGET
    try:
        return max(0.1, float(argv[idx + 1]))
    except ValueError:
        return TIME_BUDGET


def _extract_approach(argv):
    # parse --approach value from argv, supports aliases like "genetic" -> "ga"
    if "--approach" not in argv:
        return "alns"
    idx = argv.index("--approach")
    if idx + 1 >= len(argv):
        return "ga"
    raw = argv[idx + 1].strip().lower()
    aliases = {
        "topological": "topo_seq",
        "topological_baseline": "topo_seq",
        "topological_sequential": "topo_seq",
        "id": "id_ssgs",
        "ssgs_id": "id_ssgs",
        "lft": "lft_ssgs",
        "ssgs_lft": "lft_ssgs",
        "genetic": "ga",
        "genetic_algorithm": "ga",
        "adaptive_large_neighborhood_search": "alns",
        "alns_ssgs": "alns",
    }
    return aliases.get(raw, raw)


def _worker_optimize(task):
    # single worker for multiprocessing portfolio, each gets a different random seed
    filepath, seed, time_budget, approach = task
    random.seed(seed)

    project = parse(filepath)
    if approach == "alns":
        schedule = alns_optimize(project, time_limit=time_budget)
    else:
        schedule = genetic_algorithm(project, time_limit=time_budget)
    makespan = get_makespan(project, schedule)
    return makespan, schedule


def solve(filepath, workers=1, time_budget=TIME_BUDGET, approach="ga"):
    # full pipeline: parse -> feasibility check -> optimize -> return best schedule
    project = parse(filepath)

    # Bail out immediately if any activity exceeds resource capacity.
    if not check_feasibility(project):
        return project, None

    if approach == "topo_seq":
        return project, topological_sequential_schedule(project)

    if approach == "id_ssgs":
        return project, ssgs(project, order_by_id(project))

    if approach == "lft_ssgs":
        return project, ssgs(project, order_by_lft(project))

    # Metaheuristics portfolio with LFT baseline safety net.
    baseline_order = order_by_lft(project)
    best_schedule = ssgs(project, baseline_order)
    best_makespan = get_makespan(project, best_schedule)

    # step 2: try to improve with the optimizer
    if workers <= 1:
        try:
            if approach == "alns":
                optimized = alns_optimize(project, time_limit=time_budget)
            else:
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
        tasks = [(filepath, base_seed + i * 9973, time_budget, approach) for i in range(workers)]
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
                if approach == "alns":
                    optimized = alns_optimize(project, time_limit=time_budget)
                else:
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
    # print schedule in a readable table format
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
        print("optional: --approach <ga|alns|lft_ssgs|id_ssgs|topo_seq>")
        sys.exit(1)

    workers = _extract_workers(sys.argv)
    time_budget = _extract_time_budget(sys.argv)
    approach = _extract_approach(sys.argv)

    if sys.argv[1] == "--batch":
        # batch mode — run all instances in a folder
        folder = sys.argv[2] if len(sys.argv) > 2 else "../sm_j10"
        print(
            f"batch config: workers={workers}, time_budget={time_budget:.2f}s, approach={approach} ({APPROACH_LABELS.get(approach, approach)})",
            file=sys.stderr,
        )
        test_all_instances(
            folder,
            lambda fp: solve(fp, workers=workers, time_budget=time_budget, approach=approach),
        )
    else:
        # single instance mode
        filepath = sys.argv[1]
        start = time.time()

        project, schedule = solve(filepath, workers=workers, time_budget=time_budget, approach=approach)
        elapsed = time.time() - start

        if schedule is None:
            # Submission format: print -1 for infeasible instances
            print("-1")
            print(f"infeasible (activity resource demand exceeds capacity)", file=sys.stderr)
            print(f"time: {elapsed:.2f}s", file=sys.stderr)
        else:
            # Submission format: comma-separated start times for activities 1..N
            start_times = [str(schedule[i]) for i in range(1, project.n + 1)]
            print(", ".join(start_times))

            # Everything else goes to stderr so it doesn't interfere with grading
            valid, violations = validate(project, schedule)
            makespan = compute_makespan(project, schedule)
            print(f"makespan={makespan} valid={valid} time={elapsed:.2f}s", file=sys.stderr)
            print(f"workers={workers} approach={approach} ({APPROACH_LABELS.get(approach, approach)})", file=sys.stderr)
            if not valid:
                for v in violations[:10]:
                    print(f"  {v}", file=sys.stderr)


if __name__ == "__main__":
    main()
