#!/usr/bin/env python3
"""Batch runner for J10/J20 instances"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import solve
from validator import validate, compute_makespan

# Accept folder as command-line argument
if len(sys.argv) > 1:
    folder = sys.argv[1]
else:
    folder = './sm_j10'

if not os.path.isdir(folder):
    print(f"Error: folder '{folder}' not found")
    sys.exit(1)

sch_files = sorted([f for f in os.listdir(folder) if f.endswith('.SCH')])

num_valid = 0
num_infeasible = 0
num_suspicious = 0
total_makespan = 0
best_makespan = float('inf')
worst_makespan = 0
best_instance = None
worst_instance = None

batch_start = time.time()
print(f"Found {len(sch_files)} instances\n", flush=True)

for idx, filename in enumerate(sch_files, 1):
    filepath = os.path.join(folder, filename)
    start = time.time()

    try:
        project, schedule = solve(filepath)
        elapsed = time.time() - start

        valid, violations = validate(project, schedule)
        makespan = compute_makespan(project, schedule)

        if valid:
            if makespan > 100:
                num_suspicious += 1
                status = "SUSP"
            else:
                num_valid += 1
                total_makespan += makespan
                if makespan < best_makespan:
                    best_makespan = makespan
                    best_instance = filename
                if makespan > worst_makespan:
                    worst_makespan = makespan
                    worst_instance = filename
                status = "OK"
        else:
            num_infeasible += 1
            status = "NO"

        if idx % 10 == 0:
            elapsed_total = time.time() - batch_start
            rate = idx / elapsed_total
            remaining = (len(sch_files) - idx) / rate if rate > 0 else 0
            print(f"[{idx:3d}/{len(sch_files)}] {filename}: makespan={makespan:3d} {status}  ETA: {remaining/60:.1f}m", flush=True)
        else:
            print(f"[{idx:3d}/{len(sch_files)}] {filename}: makespan={makespan:3d} {status}", flush=True)

    except Exception as e:
        print(f"[{idx:3d}/{len(sch_files)}] {filename}: ERROR - {str(e)[:40]}", flush=True)
        num_infeasible += 1

batch_end = time.time()
batch_duration = batch_end - batch_start

print(f"\n{'='*70}", flush=True)
print(f"RESULTS SUMMARY:", flush=True)
print(f"{'='*70}", flush=True)

print(f"\nGOOD SOLUTIONS: {num_valid}/{len(sch_files)} ({100*num_valid/len(sch_files):.1f}%)", flush=True)
if num_valid > 0:
    print(f"  Average makespan: {total_makespan/num_valid:.1f}", flush=True)
    print(f"  Best:             {best_makespan} ({best_instance})", flush=True)
    print(f"  Worst:            {worst_makespan} ({worst_instance})", flush=True)

print(f"\nSUSPICIOUS (makespan > 100): {num_suspicious}/{len(sch_files)} ({100*num_suspicious/len(sch_files):.1f}%)", flush=True)

print(f"\nINVALID: {num_infeasible}/{len(sch_files)} ({100*num_infeasible/len(sch_files):.1f}%)", flush=True)

print(f"\n{'='*70}", flush=True)
print(f"Total time: {batch_duration:.1f}s ({batch_duration/60:.1f}m)", flush=True)
print(f"Avg time per instance: {batch_duration/len(sch_files):.2f}s", flush=True)
print(f"{'='*70}", flush=True)
