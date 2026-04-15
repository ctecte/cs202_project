# RCPSP Interactive Experiment Summary

## Configuration

- Folders: sm_j10, sm_j20
- Time budget per instance: 28.0s
- Instance limit: all

## Run Plan

| Run ID       | Approach Code | Approach Name                                     | Workers |
| ------------ | ------------- | ------------------------------------------------- | ------: |
| alns_run1_w1 | alns          | Adaptive Large Neighborhood Search + SSGS Decoder | 1       |

## Aggregate Results

| Folder | Run ID       | Approach                                          | Workers | Instances | Valid | Invalid | Infeasible | Errors | Avg Runtime (s) | Avg Makespan (valid only) |
| ------ | ------------ | ------------------------------------------------- | ------: | --------: | ----: | ------: | ---------: | -----: | --------------: | ------------------------: |
| sm_j10 | alns_run1_w1 | Adaptive Large Neighborhood Search + SSGS Decoder | 1       | 270       | 253   | 17      | 17         | 0      | 26.244          | 36.6008                   |
| sm_j20 | alns_run1_w1 | Adaptive Large Neighborhood Search + SSGS Decoder | 1       | 270       | 266   | 4       | 4          | 0      | 27.6964         | 57.609                    |