# How To Run

## Where The Approach Code Lives

- `topo_seq` (Topological Sequential Baseline): `src/scheduler.py`
  - function: `topological_sequential_schedule(project)`
- `id_ssgs` (SSGS with Activity-ID priority): `src/scheduler.py`
  - function: `order_by_id(project)` and then `ssgs(project, order)`
- `lft_ssgs` (SSGS with Latest Finish Time priority): `src/scheduler.py`
  - function: `order_by_lft(project)` and then `ssgs(project, order)`
- `ga` (Genetic Algorithm + SSGS decoder): `src/optimizer.py`
  - function: `genetic_algorithm(project, time_limit=...)`
- Approach selection / routing is in `src/main.py`
  - function: `solve(filepath, workers=..., time_budget=..., approach=...)`

## Single Instance Runs

Run from project root.

```powershell
python src/main.py sm_j10/PSP1.SCH --approach topo_seq --workers 1 --time-budget 10
python src/main.py sm_j10/PSP1.SCH --approach id_ssgs --workers 1 --time-budget 10
python src/main.py sm_j10/PSP1.SCH --approach lft_ssgs --workers 1 --time-budget 10
python src/main.py sm_j10/PSP1.SCH --approach ga --workers 1 --time-budget 10
```

You can also use aliases:
- `topological` -> `topo_seq`
- `id` -> `id_ssgs`
- `lft` -> `lft_ssgs`
- `genetic` -> `ga`

Example:

```powershell
python src/main.py sm_j20/PSP255.SCH --approach genetic --workers 4 --time-budget 28
```

## Batch Runs (One Approach At A Time)

```powershell
python src/main.py --batch sm_j10 --approach topo_seq --workers 1 --time-budget 10
python src/main.py --batch sm_j10 --approach id_ssgs --workers 1 --time-budget 10
python src/main.py --batch sm_j10 --approach lft_ssgs --workers 1 --time-budget 10
python src/main.py --batch sm_j10 --approach ga --workers 4 --time-budget 28
```

## Experiment Runs (Recommended For Report)

This generates machine specs + per-instance + aggregate CSV + summary markdown.

```powershell
python src/experiments.py --folders sm_j10 sm_j20 --approaches topo_seq id_ssgs lft_ssgs ga --time-budget 28 --workers 1
```

Using easy aliases:

```powershell
python src/experiments.py --folders sm_j10 sm_j20 --approaches topological id lft genetic --time-budget 28 --workers 1
```

Quick smoke test:

```powershell
python src/experiments.py --folders sm_j10 --approaches topological lft genetic --time-budget 5 --workers 1 --limit 10
```

## Where Experiment Output Is Saved

Each run creates:

- `experiments/<timestamp>/machine_specs.json`
- `experiments/<timestamp>/results_per_instance.csv`
- `experiments/<timestamp>/results_aggregate.csv`
- `experiments/<timestamp>/summary.md`

## Worker Notes

- `topo_seq`, `id_ssgs`, `lft_ssgs` are deterministic single-construction methods; `workers` has no practical effect there.
- `ga` uses `workers` for portfolio parallelism on the same instance: each worker runs GA with a different random seed and the best result is selected.
