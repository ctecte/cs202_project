# RCPSP Interactive Experiment Summary

## Configuration

- Folders: sm_j10, sm_j20
- Time budget per instance: 28.0s
- Instance limit: all

## Run Plan

| Run ID           | Approach Code | Approach Name                                                   | Workers |
| ---------------- | ------------- | --------------------------------------------------------------- | ------: |
| topo_seq_run1_w1 | topo_seq      | Topological Sequential Baseline (precedence-only)               | 1       |
| id_ssgs_run1_w1  | id_ssgs       | Serial Schedule Generation Scheme (Priority by Activity ID)     | 1       |
| lft_ssgs_run1_w1 | lft_ssgs      | Serial Schedule Generation Scheme (Latest Finish Time priority) | 1       |
| ga_run1_w1       | ga            | Genetic Algorithm + SSGS Decoder                                | 1       |
| ga_run2_w2       | ga            | Genetic Algorithm + SSGS Decoder                                | 2       |
| ga_run3_w4       | ga            | Genetic Algorithm + SSGS Decoder                                | 4       |
| ga_run4_w8       | ga            | Genetic Algorithm + SSGS Decoder                                | 8       |

## Aggregate Results

| Folder | Run ID           | Approach                                                        | Workers | Instances | Valid | Invalid | Infeasible | Errors | Avg Runtime (s) | Avg Makespan (valid only) |
| ------ | ---------------- | --------------------------------------------------------------- | ------: | --------: | ----: | ------: | ---------: | -----: | --------------: | ------------------------: |
| sm_j10 | ga_run1_w1       | Genetic Algorithm + SSGS Decoder                                | 1       | 270       | 253   | 17      | 17         | 0      | 0.2971          | 36.6047                   |
| sm_j10 | ga_run2_w2       | Genetic Algorithm + SSGS Decoder                                | 2       | 270       | 253   | 17      | 17         | 0      | 0.6142          | 36.6008                   |
| sm_j10 | ga_run3_w4       | Genetic Algorithm + SSGS Decoder                                | 4       | 270       | 253   | 17      | 17         | 0      | 0.813           | 36.6008                   |
| sm_j10 | ga_run4_w8       | Genetic Algorithm + SSGS Decoder                                | 8       | 270       | 253   | 17      | 17         | 0      | 1.1925          | 36.6008                   |
| sm_j10 | id_ssgs_run1_w1  | Serial Schedule Generation Scheme (Priority by Activity ID)     | 1       | 270       | 253   | 17      | 17         | 0      | 0.0003          | 40.7233                   |
| sm_j10 | lft_ssgs_run1_w1 | Serial Schedule Generation Scheme (Latest Finish Time priority) | 1       | 270       | 253   | 17      | 17         | 0      | 0.0004          | 40.1621                   |
| sm_j10 | topo_seq_run1_w1 | Topological Sequential Baseline (precedence-only)               | 1       | 270       | 253   | 17      | 17         | 0      | 0.003           | 55.2134                   |
| sm_j20 | ga_run1_w1       | Genetic Algorithm + SSGS Decoder                                | 1       | 270       | 266   | 4       | 4          | 0      | 1.2093          | 58.7143                   |
| sm_j20 | ga_run2_w2       | Genetic Algorithm + SSGS Decoder                                | 2       | 270       | 266   | 4       | 4          | 0      | 1.6731          | 58.3609                   |
| sm_j20 | ga_run3_w4       | Genetic Algorithm + SSGS Decoder                                | 4       | 270       | 266   | 4       | 4          | 0      | 2.2823          | 58.1203                   |
| sm_j20 | ga_run4_w8       | Genetic Algorithm + SSGS Decoder                                | 8       | 270       | 266   | 4       | 4          | 0      | 3.6646          | 57.8947                   |
| sm_j20 | id_ssgs_run1_w1  | Serial Schedule Generation Scheme (Priority by Activity ID)     | 1       | 270       | 266   | 4       | 4          | 0      | 0.0007          | 69.8383                   |
| sm_j20 | lft_ssgs_run1_w1 | Serial Schedule Generation Scheme (Latest Finish Time priority) | 1       | 270       | 266   | 4       | 4          | 0      | 0.0008          | 68.3759                   |
| sm_j20 | topo_seq_run1_w1 | Topological Sequential Baseline (precedence-only)               | 1       | 270       | 266   | 4       | 4          | 0      | 0.0027          | 110.5902                  |