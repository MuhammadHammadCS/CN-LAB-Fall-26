**Table 1 - single run, seed=544 (200 packets, N=4, k=3)**

| Scenario | Protocol | Transmitted | Retransmissions | Delivered | Time (s) | Throughput (kbps) |
|---|---|---|---|---|---|---|
| A: Reliable | GBN | 200.0 | 0.0 | 200 | 25.22 | 63.44 |
| A: Reliable | SR | 200.0 | 0.0 | 200 | 25.22 | 63.44 |
| B: Loss 0.10 | GBN | 280.0 | 80.0 | 200 | 50.91 | 31.43 |
| B: Loss 0.10 | SR | 248.0 | 48.0 | 200 | 54.74 | 29.23 |
| C: Mixed (L.05/C.05/D.10) | GBN | 310.0 | 110.0 | 200 | 61.08 | 26.20 |
| C: Mixed (L.05/C.05/D.10) | SR | 259.0 | 59.0 | 200 | 64.56 | 24.78 |

**Table 2 - average of 20 runs, seeds 544..563**

| Scenario | Protocol | Transmitted | Retransmissions | Delivered | Time (s) | Throughput (kbps) |
|---|---|---|---|---|---|---|
| A: Reliable | GBN | 200.0 | 0.0 | 200 | 25.22 | 63.44 |
| A: Reliable | SR | 200.0 | 0.0 | 200 | 25.22 | 63.44 |
| B: Loss 0.10 | GBN | 291.2 | 91.2 | 200 | 53.75 | 30.12 |
| B: Loss 0.10 | SR | 246.6 | 46.6 | 200 | 54.79 | 29.39 |
| C: Mixed (L.05/C.05/D.10) | GBN | 352.6 | 152.6 | 200 | 75.60 | 21.36 |
| C: Mixed (L.05/C.05/D.10) | SR | 247.7 | 47.7 | 200 | 57.51 | 28.02 |
