# RCPSP Interactive Experiment Summary

## Configuration

- Folders: sm_j10
- Time budget per instance: 28.0s
- Instance limit: all

## Run Plan

| Run ID        | Approach Code | Approach Name                                     | Workers |
| ------------- | ------------- | ------------------------------------------------- | ------: |
| ga_run1_w12   | ga            | Genetic Algorithm + SSGS Decoder                  | 12      |
| alns_run1_w12 | alns          | Adaptive Large Neighborhood Search + SSGS Decoder | 12      |

## Aggregate Results

| Folder | Run ID        | Approach                                          | Workers | Instances | Valid | Invalid | Infeasible | Errors | Avg Runtime (s) | Avg Makespan (valid only) |
| ------ | ------------- | ------------------------------------------------- | ------: | --------: | ----: | ------: | ---------: | -----: | --------------: | ------------------------: |
| sm_j10 | alns_run1_w12 | Adaptive Large Neighborhood Search + SSGS Decoder | 12      | 270       | 253   | 17      | 17         | 0      | 29.9516         | 36.6008                   |
| sm_j10 | ga_run1_w12   | Genetic Algorithm + SSGS Decoder                  | 12      | 270       | 253   | 17      | 17         | 0      | 2.0172          | 36.6008                   |