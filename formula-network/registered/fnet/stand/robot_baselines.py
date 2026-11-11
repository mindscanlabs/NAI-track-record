"""The authors' GP models on the Panda test trajectories (their published estimates): nMSE per joint.

nMSE (%) = 100 * mean((y - y_hat)^2) / var(y) per test trajectory, then the mean over the 16 test trajectories
and the 12 training combinations (the paper's protocol). Also checks that their Y is our tau column.
    python -I robot_baselines.py
"""
import csv
import sys
from collections import defaultdict

import numpy as np

D = "D:/Claude/nai-data/fnet/robot"


def table(seed):
    with open(f"{D}/tables/panda_seed{seed:02d}.csv") as f:
        r = csv.reader(f)
        head = next(r)
        a = np.array([[float(v) for v in row] for row in r])
    return head, a


def main():
    idx = list(csv.DictReader(open(f"{D}/baselines/estimates_index.tsv"), delimiter="\t"))
    tau = {}
    res = defaultdict(list)          # model -> list of per-trajectory nMSE vectors (7)
    worst_align = 0.0
    for e in idx:
        seed = int(e["seed"])
        if seed not in tau:
            head, a = table(seed)
            tau[seed] = a[:, [head.index(f"tau_{j}") for j in range(1, 8)]].T
        z = np.load(f"{D}/baselines/{e['file']}")
        y, yh = z["Y"], z["Y_hat"]
        t = tau[seed]
        n = min(y.shape[1], t.shape[1])
        if y.shape[1] != t.shape[1]:
            print("length differs", e["file"], y.shape, t.shape, file=sys.stderr)
        worst_align = max(worst_align, float(np.max(np.abs(y[:, :n] - t[:, :n]))))
        nm = 100.0 * np.mean((y - yh) ** 2, axis=1) / np.var(y, axis=1)
        res[e["model"]].append(nm)
    print(f"max |Y - tau| over all files: {worst_align:.3g}")
    print("model".ljust(40), " ".join(f"j{j}".rjust(7) for j in range(1, 8)), "  mean")
    for m, v in sorted(res.items()):
        v = np.array(v)
        print(m.ljust(40), " ".join(f"{x:7.3f}" for x in v.mean(axis=0)), f"{v.mean():7.3f}", f"(n={len(v)})")


if __name__ == "__main__":
    main()
