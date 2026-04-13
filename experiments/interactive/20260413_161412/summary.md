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
| ga_run2_w4       | ga            | Genetic Algorithm + SSGS Decoder                                | 4       |
| ga_run3_w12      | ga            | Genetic Algorithm + SSGS Decoder                                | 12      |

## Aggregate Results

| Folder | Run ID           | Approach                                                        | Workers | Instances | Valid | Invalid | Avg Runtime (s) | Avg Makespan (valid only) |
| ------ | ---------------- | --------------------------------------------------------------- | ------: | --------: | ----: | ------: | --------------: | ------------------------: |
| sm_j10 | ga_run1_w1       | Genetic Algorithm + SSGS Decoder                                | 1       | 270       | 253   | 17      | 0.3074          | 36.6087                   |
| sm_j10 | ga_run2_w4       | Genetic Algorithm + SSGS Decoder                                | 4       | 270       | 253   | 17      | 0.5768          | 36.6324                   |
| sm_j10 | ga_run3_w12      | Genetic Algorithm + SSGS Decoder                                | 12      | 270       | 253   | 17      | 1.2288          | 36.6008                   |
| sm_j10 | id_ssgs_run1_w1  | Serial Schedule Generation Scheme (Priority by Activity ID)     | 1       | 270       | 253   | 17      | 0.0003          | 40.7233                   |
| sm_j10 | lft_ssgs_run1_w1 | Serial Schedule Generation Scheme (Latest Finish Time priority) | 1       | 270       | 253   | 17      | 0.0004          | 40.1621                   |
| sm_j10 | topo_seq_run1_w1 | Topological Sequential Baseline (precedence-only)               | 1       | 270       | 253   | 17      | 0.0003          | 55.2134                   |
| sm_j20 | ga_run1_w1       | Genetic Algorithm + SSGS Decoder                                | 1       | 270       | 266   | 4       | 1.0342          | 58.9511                   |
| sm_j20 | ga_run2_w4       | Genetic Algorithm + SSGS Decoder                                | 4       | 270       | 266   | 4       | 1.5408          | 58.2669                   |
| sm_j20 | ga_run3_w12      | Genetic Algorithm + SSGS Decoder                                | 12      | 270       | 266   | 4       | 3.5872          | 57.9286                   |
| sm_j20 | id_ssgs_run1_w1  | Serial Schedule Generation Scheme (Priority by Activity ID)     | 1       | 270       | 266   | 4       | 0.0007          | 69.8383                   |
| sm_j20 | lft_ssgs_run1_w1 | Serial Schedule Generation Scheme (Latest Finish Time priority) | 1       | 270       | 266   | 4       | 0.0007          | 68.3759                   |
| sm_j20 | topo_seq_run1_w1 | Topological Sequential Baseline (precedence-only)               | 1       | 270       | 266   | 4       | 0.0003          | 110.5902                  |