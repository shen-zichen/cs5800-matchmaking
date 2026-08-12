# Matching Scalability Test Results

Execution time of the Max-Flow lane matching (`solve_lane_matching`, capacity=2) as the candidate pool size P grows.

Each point is the mean of 30 repeated runs on a fixed-seed (seed=42) random pool. Timing includes the internal deepcopy that keeps the call side-effect-free; that deepcopy is itself O(P), so the measured growth remains polynomial.

| Pool Size (P) | Mean Execution Time (ms) |
| :---: | :---: |
| 10 | 0.0994 |
| 20 | 0.1896 |
| 50 | 0.4034 |
| 100 | 0.8329 |
| 200 | 2.0952 |
| 400 | 3.3821 |
| 600 | 4.6560 |
| 800 | 6.1844 |
| 1200 | 9.3376 |
| 1600 | 12.1296 |
| 2400 | 18.7790 |
| 3200 | 24.3244 |

## Conclusion
Runtime grows approximately linearly with P (doubling P roughly doubles the time), confirming the feasibility check is polynomial-time. This is what makes pooling from a large queue tractable: verifying whether a candidate window is lane-feasible stays cheap even for large P.
