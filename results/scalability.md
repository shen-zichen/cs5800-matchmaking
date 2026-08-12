# Matching Scalability Test Results

This document records the execution time of the Max-Flow Lane Matching algorithm 
as the candidate pool size P grows from 10 to 1000 players.


| Pool Size (P) | Average Execution Time (ms) | Efficiency Level |
| :---: | :---: | :---: |
| 10 | 0.0845 ms | < 1 ms (Ultra Fast) |
| 20 | 0.1557 ms | < 1 ms (Ultra Fast) |
| 50 | 0.3535 ms | < 1 ms (Ultra Fast) |
| 100 | 0.6332 ms | < 1 ms (Ultra Fast) |
| 200 | 1.2097 ms | < 10 ms (Fast) |
| 500 | 2.7667 ms | < 10 ms (Fast) |
| 1000 | 5.4983 ms | < 10 ms (Fast) |


## Conclusion
The scalability test results demonstrate that even when the pool size grows to 1000 players, the Max-Flow matching algorithm finishes within ~5.5 ms, validating the polynomial time complexity of the feasibility check.
