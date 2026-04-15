# RCPSP Interactive Experiment Summary

## Configuration

- Folders: sm_j10, sm_j20
- Time budget per instance: 28.0s
- Instance limit: all

## Run Plan

| Run ID       | Approach Code | Approach Name                                     | Workers |
| ------------ | ------------- | ------------------------------------------------- | ------: |
| alns_run1_w4 | alns          | Adaptive Large Neighborhood Search + SSGS Decoder | 4       |

## Aggregate Results

| Folder | Run ID       | Approach                                          | Workers | Instances | Valid | Invalid | Infeasible | Errors | Avg Runtime (s) | Avg Makespan (valid only) |
| ------ | ------------ | ------------------------------------------------- | ------: | --------: | ----: | ------: | ---------: | -----: | --------------: | ------------------------: |
| sm_j10 | alns_run1_w4 | Adaptive Large Neighborhood Search + SSGS Decoder | 4       | 270       | 253   | 17      | 17         | 0      | 27.063          | 36.6008                   |
| sm_j20 | alns_run1_w4 | Adaptive Large Neighborhood Search + SSGS Decoder | 4       | 270       | 266   | 4       | 4          | 0      | 28.3979         | 57.4925                   |