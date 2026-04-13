"""
Experiment runner for RCPSP project report requirements.

Outputs:
- per-run CSV with solution quality + runtime
- aggregate CSV by approach
- machine specs JSON
- short markdown summary
"""

import argparse
import csv
import datetime as dt
import json
import os
import platform
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from main import solve
from validator import validate, compute_makespan


APPROACHES = ("topo_seq", "id_ssgs", "lft_ssgs", "ga")

APPROACH_LABELS = {
    "topo_seq": "Topological Sequential Baseline (precedence-only)",
    "id_ssgs": "Serial Schedule Generation Scheme (Priority by Activity ID)",
    "lft_ssgs": "Serial Schedule Generation Scheme (Latest Finish Time priority)",
    "ga": "Genetic Algorithm + SSGS Decoder",
}

APPROACH_ALIASES = {
    "topological": "topo_seq",
    "topological_baseline": "topo_seq",
    "topological_sequential": "topo_seq",
    "id": "id_ssgs",
    "ssgs_id": "id_ssgs",
    "lft": "lft_ssgs",
    "ssgs_lft": "lft_ssgs",
    "genetic": "ga",
    "genetic_algorithm": "ga",
}


def normalize_approach(name):
    key = name.strip().lower()
    return APPROACH_ALIASES.get(key, key)


def natural_psp_key(name):
    stem = os.path.splitext(name)[0]
    m = re.search(r"([0-9]+)$", stem)
    if m:
        return (int(m.group(1)), name)
    return (10**9, name)


def get_machine_specs():
    specs = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count_logical": os.cpu_count(),
    }

    # Best-effort memory query without external dependencies.
    try:
        if platform.system().lower() == "windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            specs["ram_bytes"] = int(stat.ullTotalPhys)
            specs["ram_gb"] = round(stat.ullTotalPhys / (1024**3), 2)
    except Exception:
        pass

    return specs


def list_instances(folder, limit=None):
    files = sorted([f for f in os.listdir(folder) if f.endswith(".SCH")], key=natural_psp_key)
    if limit is not None and limit > 0:
        files = files[:limit]
    return [os.path.join(folder, f) for f in files]


def run_experiment(folder, approach, time_budget, workers, limit=None):
    rows = []
    approach_name = APPROACH_LABELS.get(approach, approach)
    for path in list_instances(folder, limit=limit):
        name = os.path.basename(path)
        t0 = time.time()
        try:
            project, schedule = solve(path, workers=workers, time_budget=time_budget, approach=approach)
            elapsed = time.time() - t0
            valid, violations = validate(project, schedule)
            makespan = compute_makespan(project, schedule)
            rows.append(
                {
                    "instance": name,
                    "folder": folder,
                    "approach": approach,
                    "approach_name": approach_name,
                    "time_budget": time_budget,
                    "workers": workers,
                    "runtime_sec": round(elapsed, 4),
                    "makespan": makespan,
                    "valid": bool(valid),
                    "status": "OK" if valid else "INVALID",
                    "error": "" if valid else " | ".join(violations[:3]),
                }
            )
        except Exception as e:
            elapsed = time.time() - t0
            rows.append(
                {
                    "instance": name,
                    "folder": folder,
                    "approach": approach,
                    "approach_name": approach_name,
                    "time_budget": time_budget,
                    "workers": workers,
                    "runtime_sec": round(elapsed, 4),
                    "makespan": -1,
                    "valid": False,
                    "status": "ERROR",
                    "error": str(e),
                }
            )
    return rows


def aggregate_rows(rows):
    grouped = {}
    for row in rows:
        key = (row["folder"], row["approach"])
        grouped.setdefault(key, []).append(row)

    agg = []
    for (folder, approach), vals in grouped.items():
        approach_name = APPROACH_LABELS.get(approach, approach)
        valid = [v for v in vals if v["valid"]]
        avg_runtime = sum(v["runtime_sec"] for v in vals) / max(1, len(vals))
        avg_makespan = (
            sum(v["makespan"] for v in valid) / len(valid)
            if valid
            else None
        )
        agg.append(
            {
                "folder": folder,
                "approach": approach,
                "approach_name": approach_name,
                "instances": len(vals),
                "valid_count": len(valid),
                "invalid_count": len(vals) - len(valid),
                "avg_runtime_sec": round(avg_runtime, 4),
                "avg_makespan_valid": round(avg_makespan, 4) if avg_makespan is not None else "NA",
            }
        )
    return sorted(agg, key=lambda x: (x["folder"], x["approach"]))


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def write_markdown_summary(path, aggregate, machine_specs, args):
    lines = []
    lines.append("# RCPSP Experiment Summary")
    lines.append("")
    lines.append("## Run Configuration")
    lines.append("")
    lines.append(f"- Folders: {', '.join(args.folders)}")
    lines.append(f"- Approaches: {', '.join(args.approaches)}")
    lines.append(f"- Time budget per instance: {args.time_budget}s")
    lines.append(f"- Workers: {args.workers}")
    lines.append(f"- Instance limit: {args.limit if args.limit else 'all'}")
    lines.append("")
    lines.append("## Machine Specs")
    lines.append("")
    for k in sorted(machine_specs.keys()):
        lines.append(f"- {k}: {machine_specs[k]}")
    lines.append("")
    lines.append("## Aggregate Results")
    lines.append("")
    lines.append("| Folder | Approach Code | Approach Name | Instances | Valid | Invalid | Avg Runtime (s) | Avg Makespan (valid only) |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for row in aggregate:
        lines.append(
            f"| {row['folder']} | {row['approach']} | {row['approach_name']} | {row['instances']} | {row['valid_count']} | {row['invalid_count']} | {row['avg_runtime_sec']} | {row['avg_makespan_valid']} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `topo_seq` (Topological Sequential Baseline): Build a precedence-feasible order, then schedule one activity at a time. Rationale: intentionally weak baseline for comparison.")
    lines.append("- `id_ssgs` (SSGS with Activity-ID Priority): Earliest feasible scheduling with simple ID tie-breaking. Rationale: deterministic resource-feasible baseline.")
    lines.append("- `lft_ssgs` (SSGS with Latest Finish Time Priority): Earliest feasible scheduling guided by urgency (latest finish time). Rationale: stronger heuristic with low overhead.")
    lines.append("- `ga` (Genetic Algorithm + SSGS Decoder): Metaheuristic search over activity orders, decoded by SSGS. Rationale: can improve quality at higher compute cost.")
    lines.append("")
    lines.append("Interpretation tip: lower makespan is better quality; runtime shows efficiency trade-offs.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def parse_args():
    ap = argparse.ArgumentParser(description="Run comparative RCPSP experiments and export report artifacts.")
    ap.add_argument("--folders", nargs="+", default=["sm_j10", "sm_j20"], help="Dataset folders to benchmark")
    ap.add_argument("--approaches", nargs="+", default=list(APPROACHES), help="Approach codes or aliases")
    ap.add_argument("--time-budget", type=float, default=28.0)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="Optional number of instances per folder")
    ap.add_argument("--out-dir", default="experiments")
    return ap.parse_args()


def main():
    args = parse_args()
    args.approaches = [normalize_approach(a) for a in args.approaches]
    unknown = [a for a in args.approaches if a not in APPROACHES]
    if unknown:
        raise ValueError(f"Unknown approach(es): {unknown}. Valid: {list(APPROACHES)}")
    os.makedirs(args.out_dir, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.out_dir, stamp)
    os.makedirs(run_dir, exist_ok=True)

    machine_specs = get_machine_specs()
    with open(os.path.join(run_dir, "machine_specs.json"), "w", encoding="utf-8") as f:
        json.dump(machine_specs, f, indent=2)

    all_rows = []
    limit = args.limit if args.limit > 0 else None

    for folder in args.folders:
        for approach in args.approaches:
            print(f"running folder={folder}, approach={approach}")
            rows = run_experiment(
                folder=folder,
                approach=approach,
                time_budget=args.time_budget,
                workers=args.workers,
                limit=limit,
            )
            all_rows.extend(rows)

    per_instance_fields = [
        "instance",
        "folder",
        "approach",
        "approach_name",
        "time_budget",
        "workers",
        "runtime_sec",
        "makespan",
        "valid",
        "status",
        "error",
    ]
    write_csv(os.path.join(run_dir, "results_per_instance.csv"), all_rows, per_instance_fields)

    aggregate = aggregate_rows(all_rows)
    aggregate_fields = [
        "folder",
        "approach",
        "approach_name",
        "instances",
        "valid_count",
        "invalid_count",
        "avg_runtime_sec",
        "avg_makespan_valid",
    ]
    write_csv(os.path.join(run_dir, "results_aggregate.csv"), aggregate, aggregate_fields)
    write_markdown_summary(os.path.join(run_dir, "summary.md"), aggregate, machine_specs, args)

    print("done")
    print(f"artifacts: {run_dir}")


if __name__ == "__main__":
    main()
