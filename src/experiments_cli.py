"""
Interactive CLI launcher for RCPSP experiments.

This script asks:
1) which algorithms to include,
2) how many runs per algorithm,
3) workers per algorithm run,
then executes all runs and exports consolidated artifacts.
"""

import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

import experiments as exp


ALGO_MENU = [
    ("topo_seq", "Topological Sequential Baseline (precedence-only)"),
    ("id_ssgs", "Serial Schedule Generation Scheme (Priority by Activity ID)"),
    ("lft_ssgs", "Serial Schedule Generation Scheme (Latest Finish Time priority)"),
    ("ga", "Genetic Algorithm + SSGS Decoder"),
    ("alns", "Adaptive Large Neighborhood Search + SSGS Decoder"),
]


def prompt_text(message, default=None):
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"{message}{suffix}: ").strip()
    if raw == "" and default is not None:
        return str(default)
    return raw


def prompt_int(message, default=None, min_value=None):
    while True:
        raw = prompt_text(message, default)
        try:
            value = int(raw)
            if min_value is not None and value < min_value:
                print(f"Please enter an integer >= {min_value}.")
                continue
            return value
        except ValueError:
            print("Please enter a valid integer.")


def prompt_float(message, default=None, min_value=None):
    while True:
        raw = prompt_text(message, default)
        try:
            value = float(raw)
            if min_value is not None and value < min_value:
                print(f"Please enter a number >= {min_value}.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number.")


def parse_algo_selection(raw):
    tokens = re.split(r"[\s,]+", raw.strip())
    indices = []
    for t in tokens:
        if not t:
            continue
        idx = int(t)
        if idx < 1 or idx > len(ALGO_MENU):
            raise ValueError(f"Algorithm index out of range: {idx}")
        if idx not in indices:
            indices.append(idx)
    if not indices:
        raise ValueError("No algorithms selected.")
    return [ALGO_MENU[i - 1][0] for i in indices]


def ask_algorithms_and_plan():
    print("\nSelect algorithms by number (comma-separated):")
    for i, (_, name) in enumerate(ALGO_MENU, start=1):
        print(f"  {i}. {name}")

    while True:
        try:
            raw = prompt_text("Your selection (e.g., 1,2,3,4)", "1,2,3,4")
            selected = parse_algo_selection(raw)
            break
        except Exception as e:
            print(f"Invalid selection: {e}")

    plan = []
    print("\nConfigure each selected algorithm.")
    for code in selected:
        full_name = exp.APPROACH_LABELS.get(code, code)
        runs = prompt_int(f"How many runs for {code} ({full_name})", default=1, min_value=1)
        same_workers = prompt_text("Use same worker count for all runs? (y/n)", "y").lower().startswith("y")

        if same_workers:
            w = prompt_int(f"Workers for {code}", default=1, min_value=1)
            workers_list = [w] * runs
        else:
            workers_list = []
            for r in range(1, runs + 1):
                w = prompt_int(f"Workers for {code} run {r}", default=1, min_value=1)
                workers_list.append(w)

        for r, workers in enumerate(workers_list, start=1):
            run_id = f"{code}_run{r}_w{workers}"
            plan.append(
                {
                    "run_id": run_id,
                    "approach": code,
                    "approach_name": full_name,
                    "workers": workers,
                }
            )

    return plan


def aggregate(rows):
    grouped = defaultdict(list)
    for row in rows:
        key = (row["folder"], row["run_id"], row["approach"], row["approach_name"], row["workers"])
        grouped[key].append(row)

    out = []
    for (folder, run_id, approach, approach_name, workers), vals in grouped.items():
        valid_rows = [v for v in vals if v["valid"]]
        avg_runtime = sum(v["runtime_sec"] for v in vals) / max(1, len(vals))
        avg_makespan = (
            sum(v["makespan"] for v in valid_rows) / len(valid_rows)
            if valid_rows
            else None
        )
        out.append(
            {
                "folder": folder,
                "run_id": run_id,
                "approach": approach,
                "approach_name": approach_name,
                "workers": workers,
                "instances": len(vals),
                "valid_count": len(valid_rows),
                "invalid_count": len(vals) - len(valid_rows),
                "avg_runtime_sec": round(avg_runtime, 4),
                "avg_makespan_valid": round(avg_makespan, 4) if avg_makespan is not None else "NA",
            }
        )

    return sorted(out, key=lambda x: (x["folder"], x["approach"], x["workers"], x["run_id"]))


def write_summary(path, config, aggregate_rows):
    lines = []
    lines.append("# RCPSP Interactive Experiment Summary")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- Folders: {', '.join(config['folders'])}")
    lines.append(f"- Time budget per instance: {config['time_budget']}s")
    lines.append(f"- Instance limit: {config['limit'] if config['limit'] else 'all'}")
    lines.append("")
    lines.append("## Run Plan")
    lines.append("")
    run_headers = ["Run ID", "Approach Code", "Approach Name", "Workers"]
    run_rows = [[p["run_id"], p["approach"], p["approach_name"], p["workers"]] for p in config["plan"]]
    lines.extend(exp.render_markdown_table(run_headers, run_rows, right_align_cols={3}))

    lines.append("")
    lines.append("## Aggregate Results")
    lines.append("")
    agg_headers = [
        "Folder",
        "Run ID",
        "Approach",
        "Workers",
        "Instances",
        "Valid",
        "Invalid",
        "Avg Runtime (s)",
        "Avg Makespan (valid only)",
    ]
    agg_rows = [
        [
            row["folder"],
            row["run_id"],
            row["approach_name"],
            row["workers"],
            row["instances"],
            row["valid_count"],
            row["invalid_count"],
            row["avg_runtime_sec"],
            row["avg_makespan_valid"],
        ]
        for row in aggregate_rows
    ]
    lines.extend(exp.render_markdown_table(agg_headers, agg_rows, right_align_cols={3, 4, 5, 6, 7, 8}))

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    print("RCPSP Interactive Experiment Launcher")

    folders_raw = prompt_text("Folders (comma-separated)", "sm_j10")
    folders = [x.strip() for x in folders_raw.split(",") if x.strip()]
    time_budget = prompt_float("Time budget per instance (seconds)", 28.0, min_value=0.1)
    limit = prompt_int("Instance limit per folder (0 = all)", 0, min_value=0)
    out_subdir = prompt_text("Output subfolder inside experiments", "interactive")

    plan = ask_algorithms_and_plan()

    print("\nPlanned runs:")
    for p in plan:
        print(f"- {p['run_id']}: {p['approach_name']} (workers={p['workers']})")

    go = prompt_text("Run now? (y/n)", "y").lower().startswith("y")
    if not go:
        print("Cancelled.")
        return

    experiments_root = "experiments"
    os.makedirs(experiments_root, exist_ok=True)

    out_subdir = out_subdir.strip().strip("/\\")
    if out_subdir:
        base_dir = os.path.join(experiments_root, out_subdir)
    else:
        base_dir = experiments_root
    os.makedirs(base_dir, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, stamp)
    os.makedirs(run_dir, exist_ok=True)

    machine_specs = exp.get_machine_specs()
    with open(os.path.join(run_dir, "machine_specs.json"), "w", encoding="utf-8") as f:
        json.dump(machine_specs, f, indent=2)

    all_rows = []
    run_limit = limit if limit > 0 else None

    for p in plan:
        for folder in folders:
            print(f"running folder={folder}, run={p['run_id']}")
            rows = exp.run_experiment(
                folder=folder,
                approach=p["approach"],
                time_budget=time_budget,
                workers=p["workers"],
                limit=run_limit,
            )
            for row in rows:
                row["run_id"] = p["run_id"]
            all_rows.extend(rows)

    per_instance_fields = [
        "run_id",
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
    exp.write_csv(os.path.join(run_dir, "results_per_instance.csv"), all_rows, per_instance_fields)

    agg_rows = aggregate(all_rows)
    agg_fields = [
        "folder",
        "run_id",
        "approach",
        "approach_name",
        "workers",
        "instances",
        "valid_count",
        "invalid_count",
        "avg_runtime_sec",
        "avg_makespan_valid",
    ]
    exp.write_csv(os.path.join(run_dir, "results_aggregate.csv"), agg_rows, agg_fields)

    config = {
        "folders": folders,
        "time_budget": time_budget,
        "limit": limit,
        "plan": plan,
    }
    with open(os.path.join(run_dir, "run_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    write_summary(os.path.join(run_dir, "summary.md"), config, agg_rows)

    print("\ndone")
    print(f"artifacts: {run_dir}")


if __name__ == "__main__":
    main()
