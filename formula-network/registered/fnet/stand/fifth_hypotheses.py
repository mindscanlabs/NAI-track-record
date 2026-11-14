"""The registered hypotheses of the fifth suite (docs/prereg/FNET_FIFTH.md), computed from the result files.

Relative RMSE = RMSE / RMSE of the training mean, per (table, split); non-finite predictions were replaced by the
training mean in every result file (common.metrics) and are counted here. Groups: inside = iid1; edge = xfeat, xy
(upper tails) and xfeat_lo, xy_lo (lower tails). A model's group value is the median over the group's (table, split)
pairs. H1-H5 as in the fourth registration; H6 compares v14b with v13 pair by pair; H7 tests the graded range monitor
on the network's own predictions (RESULTS/fnet_<tag>_logs).
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

from common import RESULTS, TABLES, load_splits

GROUP = {"iid1": "inside", "xfeat": "edge", "xy": "edge", "xfeat_lo": "edge", "xy_lo": "edge"}
NEAR, FAR, MIN_POINTS = 0.1, 0.25, 10


def monitor(tag, pairs):
    """Per edge pair with at least MIN_POINTS test points at distance <= NEAR and > FAR beyond the training ranges
    (the distance of fnet_range_distance, from the training rows): RMSE / sd of the training target on each zone."""
    rows = []
    for name, split in pairs:
        fn = name.replace(":", "__")
        if GROUP.get(split) != "edge":
            continue
        pth = os.path.join(RESULTS, f"fnet_{tag}_logs", f"{fn}.{split}.pred.txt")
        if not os.path.exists(pth):
            continue
        t = pd.read_csv(os.path.join(TABLES, fn + ".csv"))
        sp, _ = load_splits(fn)
        tr, te = sp[f"{split}_train"], sp[f"{split}_test"]
        X, y = t.drop(columns=["target"]).to_numpy(dtype=float), t["target"].to_numpy(dtype=float)
        lo, hi = np.nanmin(X[tr], axis=0), np.nanmax(X[tr], axis=0)
        w = np.where(hi > lo, hi - lo, 1.0)
        with np.errstate(invalid="ignore"):
            d = np.nanmax(np.maximum(np.maximum((X[te] - hi) / w, (lo - X[te]) / w), 0), axis=1)
        near, far = d <= NEAR, d > FAR
        if near.sum() < MIN_POINTS or far.sum() < MIN_POINTS:
            continue
        p = np.array([float(v) for v in open(pth).read().split()])
        p = np.where(np.isfinite(p), p, y[tr].mean())
        e, sd = y[te] - p, y[tr].std()
        rows.append({"table": fn, "split": split, "near_n": int(near.sum()), "far_n": int(far.sum()),
                     "near": np.sqrt(np.mean(e[near] ** 2)) / sd, "far": np.sqrt(np.mean(e[far] ** 2)) / sd})
    return pd.DataFrame(rows)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", default="test")
    ap.add_argument("--net", default="fnet_v14b", help="the network's model name in the result files")
    ap.add_argument("--old", default="fnet_v13", help="the previous version's model name (H6)")
    ap.add_argument("--suite", default="fifth_", help="result files prefix (another suite only for a dry run)")
    a = ap.parse_args()
    frames = [pd.read_csv(os.path.join(RESULTS, f"{a.suite}{n}_{a.side}.tsv"), sep="\t")
              for n in ("baselines", a.net, a.old)]
    r = pd.concat(frames)[["table", "split", "model", "rmse", "nonfinite"]]
    r = r[r.split.isin(list(GROUP))]
    mean = r[r.model == "mean"].set_index(["table", "split"])["rmse"]
    r = r.assign(rel=r["rmse"].to_numpy() / mean.reindex(pd.MultiIndex.from_frame(r[["table", "split"]])).to_numpy(),
                 group=r.split.map(GROUP))
    r = r[r.model != "mean"]
    med = r.pivot_table(index="model", columns="group", values="rel", aggfunc="median")
    lo_hi = r[r.group == "edge"].assign(tail=lambda d: d.split.str.endswith("_lo").map({True: "lower", False: "upper"}))
    med = med.join(lo_hi.pivot_table(index="model", columns="tail", values="rel", aggfunc="median"))
    over1 = r[r.rel > 1].groupby("model").size().reindex(med.index, fill_value=0)
    nonfinite = r[r.nonfinite > 0].groupby("model").size().reindex(med.index, fill_value=0)
    table = med.assign(pairs=r.groupby("model").size(), over1=over1, nonfinite_pairs=nonfinite, worst=r.groupby("model").rel.max())
    print(table.sort_values("edge").to_string(float_format=lambda v: "%.4f" % v))

    f, lt, mlp, ebm = med.loc[a.net], med.loc["lightgbm_tuned"], med.loc["mlp"], med.loc["ebm"]
    res = {
        "H1 edge (upper and lower tails): fnet <= tuned LightGBM":
            (f.edge <= lt.edge, f"{f.edge:.4f} vs {lt.edge:.4f}"),
        "H2 pairs worse than the mean: fnet <= tuned LightGBM":
            (over1[a.net] <= over1["lightgbm_tuned"], f"{over1[a.net]} vs {over1['lightgbm_tuned']}"),
        "H3 inside: fnet <= 1.5 x tuned LightGBM":
            (f.inside <= 1.5 * lt.inside, f"{f.inside:.4f} vs 1.5 x {lt.inside:.4f} = {1.5 * lt.inside:.4f}"),
        "H5 edge: fnet <= 1.15 x MLP and <= 1.15 x EBM":
            (f.edge <= 1.15 * mlp.edge and f.edge <= 1.15 * ebm.edge,
             f"{f.edge:.4f} vs 1.15 x {mlp.edge:.4f} = {1.15 * mlp.edge:.4f}, 1.15 x {ebm.edge:.4f} = {1.15 * ebm.edge:.4f}"),
    }
    size_path = os.path.join(RESULTS, f"{a.suite}size_{a.side}.tsv")
    if os.path.exists(size_path):
        s = pd.read_csv(size_path, sep="\t")
        speed = (s.lightgbm_ns / s.fnet_ns).median()
        res["H4 compiled C: size ratio >= 10 and speed ratio >= 3 (medians over tables)"] = (
            s.ratio.median() >= 10 and speed >= 3, f"size x{s.ratio.median():.1f}, speed x{speed:.1f}")

    # H6: v14b against v13, pair by pair over all pairs
    p = r[r.model.isin([a.net, a.old])].pivot_table(index=["table", "split"], columns="model", values="rel")
    p = p.dropna()
    lr = np.log(p[a.net] / p[a.old])
    gm = float(np.exp(lr.mean()))
    print(f"\nH6 pairs: {len(p)}; geometric mean {a.net}/{a.old} {gm:.4f}; inside "
          f"{np.exp(lr[[g == 'iid1' for _, g in p.index]].mean()):.4f}, edge {np.exp(lr[[g != 'iid1' for _, g in p.index]].mean()):.4f}")
    res["H6 v14b against v13: geometric mean of the ratio <= 1.02 and pairs worse than the mean not more"] = (
        gm <= 1.02 and over1[a.net] <= over1[a.old], f"{gm:.4f}; {over1[a.net]} vs {over1[a.old]}")

    # H7: the graded range monitor
    m = monitor(a.net.replace("fnet_", "", 1), sorted(set(zip(r.table, r.split))))
    if len(m):
        print("\nH7 pairs (RMSE / sd of the training target):\n" + m.round(4).to_string(index=False))
    up = int((m.far > m.near).sum()) if len(m) else 0
    res["H7 monitor: error at distance > 0.25 above the error at distance <= 0.1 in at least 2/3 of eligible pairs "
        "(at least 5 eligible)"] = (len(m) >= 5 and up >= 2 * len(m) / 3, f"{up} of {len(m)} pairs")
    print()
    for k, (ok, detail) in res.items():
        print(f"{'HOLDS' if ok else 'FAILS'}  {k}: {detail}")


if __name__ == "__main__":
    main()
