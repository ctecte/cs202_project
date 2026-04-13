#!/usr/bin/env python3
"""Quick batch test to find where it fails"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from parser import parse
from scheduler import ssgs, get_makespan, order_by_lft
from optimizer import genetic_algorithm
from validator import validate, compute_makespan
import time

TIME_BUDGET = 30
SAFETY_MARGIN = 0.5

def solve(filepath):
    """Minimal solve for batch testing"""
    parse_start = time.time()
    project = parse(filepath)

    baseline_start = time.time()
    baseline_order = order_by_lft(project)
    best_schedule = ssgs(project, baseline_order)
    best_makespan = get_makespan(project, best_schedule)

    opt_start = time.time()
    time_remaining = TIME_BUDGET - SAFETY_MARGIN - (time.time() - parse_start) - 2.0

    if time_remaining > 1.0:
        ga_time_limit = max(1.0, time_remaining - 1.0)
        optimized = genetic_algorithm(project, time_limit=ga_time_limit)
        if optimized:
            opt_makespan = get_makespan(project, optimized)
            if opt_makespan < best_makespan:
                best_schedule = optimized
                best_makespan = opt_makespan

    return project, best_schedule


# Test just first 120 instances
folder = './sm_j10'
sch_files = sorted([f for f in os.listdir(folder) if f.endswith('.SCH')])[:120]

print(f"Testing {len(sch_files)} instances...", flush=True)

for i, filename in enumerate(sch_files):
    filepath = os.path.join(folder, filename)

    start = time.time()
    try:
        project, schedule = solve(filepath)
        elapsed = time.time() - start

        valid, violations = validate(project, schedule)
        makespan = compute_makespan(project, schedule)

        status = "OK" if valid else f"INVALID ({len(violations)} viol)"
        print(f"  [{i+1:3d}] {filename}: ms={makespan:3d}, t={elapsed:.2f}s, {status}", flush=True)

    except Exception as e:
        elapsed = time.time() - start
        print(f"  [{i+1:3d}] {filename}: ERROR at {elapsed:.2f}s: {e}", flush=True)
        import traceback
        traceback.print_exc()
