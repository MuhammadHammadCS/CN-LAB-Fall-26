# CS3001 Assignment-II: GBN & SR Protocol Simulation

This project implements Go-Back-N (GBN) and Selective Repeat (SR) sliding window protocols over a simulated unreliable network channel, along with comparative scenario evaluations.

## Prerequisites & Setup

Ensure you have Python 3.x installed along with the required libraries for plotting and evaluation:

```
pip install matplotlib

```

## How to Run

* **Task 3 (`task3.py`)**: Runs an individual simulation of either the GBN or SR protocol with custom network conditions.

* **Task 4 (`task4.py`)**: Evaluates predefined scenarios (A, B, and C) across multiple runs, outputting performance metrics to markdown (`results.md`), CSV, and summary graphs (`results.png`, `results_avg.png`).

## Parameters

### `task3.py` Arguments

* `--protocol`: Select the protocol, either `gbn` or `sr` (**required**).

* `--packets`: Total number of packets to transmit (default: `20`).

* `--window`: Window size $N$ (default: `4`).

* `--k`: Sequence-number bits where numbers wrap mod $2^k$ (default: `3`).

* `--loss`: Probability of packet loss (default: `0.0`).

* `--corrupt`: Probability of packet corruption (default: `0.0`).

* `--delay`: Probability of extra network delay (default: `0.0`).

* `--delay-max`: Maximum extra delay duration in seconds (default: `0.2`).

* `--timeout`: Retransmission timeout in seconds (default: `1.0`).

* `--seed`: Random seed for reproducibility (default: `1234`).

* `--drop-first`: Scripted dropping of the first transmission for specific packet indices.

* `--allow-unsafe`: Bypass safety limits on window sizes.

* `--quiet`: Disable verbose per-event logging.

### `task4.py` Arguments

* `--seed`: Base random seed for scenario generation (default: `1234`).

* `--runs`: Number of simulation runs to average for statistical results (default: `20`).

## Sample Command

To run a GBN protocol simulation for 50 packets with 10% packet loss and disabled per-event logs:

```
python task3.py --protocol gbn --packets 50 --loss 0.1 --quiet
python task3.py --protocol gbn --packets 50 --loss 0.1 --seed 544
python task3.py --protocol sr --packets 50 --loss 0.2 --seed 544
python task4.py --seed 544
```