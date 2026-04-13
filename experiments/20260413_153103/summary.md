# RCPSP Experiment Summary

## Run Configuration

- Folders: sm_j10
- Approaches: topo_seq, lft_ssgs, ga
- Time budget per instance: 3.0s
- Workers: 1
- Instance limit: 2

## Machine Specs

- cpu_count_logical: 12
- machine: AMD64
- platform: Windows-10-10.0.26200-SP0
- processor: Intel64 Family 6 Model 158 Stepping 10, GenuineIntel
- python_version: 3.10.10
- ram_bytes: 17012723712
- ram_gb: 15.84
- release: 10
- system: Windows
- version: 10.0.26200

## Aggregate Results

| Folder | Approach Code | Approach Name | Instances | Valid | Invalid | Avg Runtime (s) | Avg Makespan (valid only) |
|---|---|---|---:|---:|---:|---:|---:|
| sm_j10 | ga | Genetic Algorithm + SSGS Decoder | 2 | 2 | 0 | 0.0709 | 35.5 |
| sm_j10 | lft_ssgs | Serial Schedule Generation Scheme (Latest Finish Time priority) | 2 | 2 | 0 | 0.0 | 38.0 |
| sm_j10 | topo_seq | Topological Sequential Baseline (precedence-only) | 2 | 2 | 0 | 0.0028 | 58.5 |

## Notes

- `topo_seq` (Topological Sequential Baseline):
	Build a precedence-feasible topological order and schedule exactly one activity at a time, sequentially. This ignores resource-aware optimization and overlap, so it is intentionally weak. Rationale: provides a simple lower-complexity benchmark that every stronger method should beat.
- `id_ssgs` (SSGS with Activity-ID Priority):
	Use Serial Schedule Generation Scheme and schedule each activity at its earliest feasible time, choosing eligible activities by ID order. Rationale: deterministic, resource-feasible baseline to isolate the value of better priority rules.
- `lft_ssgs` (SSGS with Latest Finish Time Priority):
	Same SSGS framework, but activity priority is based on latest finish time (more urgent activities first). Rationale: stronger heuristic than ID order; often improves makespan while staying fast and deterministic.
- `ga` (Genetic Algorithm + SSGS Decoder):
	Search over precedence-feasible activity orders using crossover/mutation, decode each candidate with SSGS, and keep the best schedule found. Rationale: trades extra runtime for potentially better solution quality than single-rule heuristics.

Interpretation tip:
- Lower average makespan is better solution quality.
- Runtime helps show efficiency trade-offs, but quality is the primary evaluation metric in your brief.