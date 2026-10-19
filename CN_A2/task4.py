"""CS3001 Assignment-II - Task 4: scenarios A, B, C for GBN and SR
Muhammad Hammad 24k-0544"""
import argparse
import csv
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from task3 import run

SCEN = {"A: Reliable": dict(loss=0.0, corrupt=0.0, delay=0.0),
        "B: Loss 0.10": dict(loss=0.10, corrupt=0.0, delay=0.0),
        "C: Mixed (L.05/C.05/D.10)": dict(loss=0.05, corrupt=0.05, delay=0.10)}
KEYS = ["transmitted", "retransmissions", "delivered", "time_s", "throughput_kbps"]


def collect(seed, runs):
    out = {}
    for sname, cfg in SCEN.items():
        for proto in ("gbn", "sr"):
            rs = [run(proto, 200, 4, 3, seed=seed + i, **cfg) for i in range(runs)]
            assert all(r["correct"] for r in rs), "a run failed to deliver correctly!"
            out[(sname, proto.upper())] = {k: st.mean(r[k] for r in rs) for k in KEYS}
    return out


def table(res, title):
    lines = [f"**{title}**", "",
             "| Scenario | Protocol | Transmitted | Retransmissions | Delivered | Time (s) | Throughput (kbps) |",
             "|---|---|---|---|---|---|---|"]
    for (s, p), r in res.items():
        lines.append(f"| {s} | {p} | {r['transmitted']:.1f} | {r['retransmissions']:.1f} | "
                     f"{r['delivered']:.0f} | {r['time_s']:.2f} | {r['throughput_kbps']:.2f} |")
    return "\n".join(lines)


def graph(res, fname, title):
    names = list(SCEN)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for a, key, lab in ((ax[0], "retransmissions", "Retransmissions (packets)"),
                        (ax[1], "throughput_kbps", "Throughput (kbps)")):
        for j, (p, c) in enumerate((("GBN", "#d95f02"), ("SR", "#1b9e77"))):
            vals = [res[(s, p)][key] for s in names]
            xs = [i + (j - 0.5) * 0.38 for i in range(len(names))]
            bars = a.bar(xs, vals, 0.38, label=p, color=c)
            a.bar_label(bars, fmt="%.1f", fontsize=8)
        a.set_xticks(range(len(names)))
        a.set_xticklabels([n.replace(" (", "\n(") for n in names], fontsize=8)
        a.set_ylabel(lab); a.legend(); a.grid(axis="y", alpha=.3)
    fig.suptitle(title)
    fig.tight_layout(); fig.savefig(fname, dpi=150)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--runs", type=int, default=20)
    x = ap.parse_args()
    single = collect(x.seed, 1)
    avg = collect(x.seed, x.runs)
    md = table(single, f"Table 1 - single run, seed={x.seed} (200 packets, N=4, k=3)") + "\n\n" + \
         table(avg, f"Table 2 - average of {x.runs} runs, seeds {x.seed}..{x.seed + x.runs - 1}")
    open("results.md", "w").write(md + "\n")
    with open("results.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["scenario", "protocol"] + KEYS)
        for (s, p), r in single.items():
            w.writerow([s, p] + [round(r[k], 3) for k in KEYS])
    graph(single, "results.png", f"GBN vs SR - 200 packets, N=4, k=3, seed={x.seed}")
    graph(avg, "results_avg.png", f"GBN vs SR - mean of {x.runs} seeds")
    print(md)