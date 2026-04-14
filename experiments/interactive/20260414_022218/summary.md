# RCPSP Interactive Experiment Summary

## Configuration

- Folders: sm_j10, sm_j20
- Time budget per instance: 28.0s
- Instance limit: all

## Run Plan

| Run ID        | Approach Code | Approach Name                                     | Workers |
| ------------- | ------------- | ------------------------------------------------- | ------: |
| ga_run1_w1    | ga            | Genetic Algorithm + SSGS Decoder                  | 1       |
| ga_run2_w12   | ga            | Genetic Algorithm + SSGS Decoder                  | 12      |
| alns_run1_w1  | alns          | Adaptive Large Neighborhood Search + SSGS Decoder | 1       |
| alns_run2_w12 | alns          | Adaptive Large Neighborhood Search + SSGS Decoder | 12      |

## Aggregate Results

| Folder | Run ID        | Approach                                          | Workers | Instances | Valid | Invalid | Avg Runtime (s) | Avg Makespan (valid only) |
| ------ | ------------- | ------------------------------------------------- | ------: | --------: | ----: | ------: | --------------: | ------------------------: |
| sm_j10 | alns_run1_w1  | Adaptive Large Neighborhood Search + SSGS Decoder | 1       | 270       | 253   | 17      | 26.2407         | 36.6008                   |
| sm_j10 | alns_run2_w12 | Adaptive Large Neighborhood Search + SSGS Decoder | 12      | 270       | 253   | 17      | 26.6034         | 36.6008                   |
| sm_j10 | ga_run1_w1    | Genetic Algorithm + SSGS Decoder                  | 1       | 270       | 253   | 17      | 0.3203          | 36.6008                   |
| sm_j10 | ga_run2_w12   | Genetic Algorithm + SSGS Decoder                  | 12      | 270       | 253   | 17      | 1.1905          | 36.6008                   |
| sm_j20 | alns_run1_w1  | Adaptive Large Neighborhood Search + SSGS Decoder | 1       | 270       | 266   | 4       | 27.6267         | 57.4774                   |
| sm_j20 | alns_run2_w12 | Adaptive Large Neighborhood Search + SSGS Decoder | 12      | 270       | 266   | 4       | 28.1189         | 57.4511                   |
| sm_j20 | ga_run1_w1    | Genetic Algorithm + SSGS Decoder                  | 1       | 270       | 266   | 4       | 1.0661          | 59.0263                   |
| sm_j20 | ga_run2_w12   | Genetic Algorithm + SSGS Decoder                  | 12      | 270       | 266   | 4       | 3.1544          | 57.9774                   |