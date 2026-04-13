# RCPSP Experiment Summary

## Run Configuration

- Folders: sm_j10
- Approaches: topo_seq, lft_ssgs, ga
- Time budget per instance: 5.0s
- Workers: 1
- Instance limit: 3

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

| Folder | Approach | Instances | Valid | Invalid | Avg Runtime (s) | Avg Makespan (valid only) |
|---|---|---:|---:|---:|---:|---:|
| sm_j10 | ga | 3 | 3 | 0 | 0.0807 | 33.0 |
| sm_j10 | lft_ssgs | 3 | 3 | 0 | 0.0 | 36.0 |
| sm_j10 | topo_seq | 3 | 3 | 0 | 0.0028 | 57.3333 |

## Notes

- `topo_seq` is the strict topological sequential baseline (precedence-only, one activity at a time).
- Compare `topo_seq` against `id_ssgs`, `lft_ssgs`, and `ga` for quality/runtime trade-off discussion.