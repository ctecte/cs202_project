# RCPSP Experiment Summary

## Run Configuration

- Folders: sm_j20
- Approaches: ga, alns
- Time budget per instance: 1.0s
- Workers: 1
- Instance limit: 10

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

| Folder | Approach Code | Approach Name                                     | Instances | Valid | Invalid | Avg Runtime (s) | Avg Makespan (valid only) |
| ------ | ------------- | ------------------------------------------------- | --------: | ----: | ------: | --------------: | ------------------------: |
| sm_j20 | alns          | Adaptive Large Neighborhood Search + SSGS Decoder | 10        | 10    | 0       | 1.0822          | 59.3                      |
| sm_j20 | ga            | Genetic Algorithm + SSGS Decoder                  | 10        | 10    | 0       | 0.5157          | 58.7                      |

## Notes

- `topo_seq` (Topological Sequential Baseline): Build a precedence-feasible order, then schedule one activity at a time. Rationale: intentionally weak baseline for comparison.
- `id_ssgs` (SSGS with Activity-ID Priority): Earliest feasible scheduling with simple ID tie-breaking. Rationale: deterministic resource-feasible baseline.
- `lft_ssgs` (SSGS with Latest Finish Time Priority): Earliest feasible scheduling guided by urgency (latest finish time). Rationale: stronger heuristic with low overhead.
- `ga` (Genetic Algorithm + SSGS Decoder): Metaheuristic search over activity orders, decoded by SSGS. Rationale: can improve quality at higher compute cost.
- `alns` (Adaptive Large Neighborhood Search + SSGS Decoder): destroy-repair metaheuristic with adaptive operator weights. Rationale: stronger intensification/diversification balance.

Interpretation tip: lower makespan is better quality; runtime shows efficiency trade-offs.