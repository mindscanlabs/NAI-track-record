"""Comparison on the common splits (iid1, xfeat, xy) of every result file of a side: baselines_<side>.tsv,
nai_*_<side>.tsv, fnet_*_<side>.tsv. Per kind of split: the median relative RMSE (RMSE / RMSE of the training
mean; 1 = no better than the mean), the median R², wins against LightGBM and against the edge constant,
the tables counted (only those where every model has a result), non-finite predictions."""
import argparse
import glob
import os

import numpy as np
import pandas as pd

from common import RESULTS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", default="work")
    ap.add_argument("--models", default="", help="comma-separated; default: all")
    ap.add_argument("--suite", default="", help="niche_ for the niche suite")
    a = ap.parse_args()
    frames = []
    base_file = os.path.join(RESULTS, f"{a.suite}baselines_{a.side}.tsv")
    for f in [base_file] + sorted(glob.glob(os.path.join(RESULTS, f"{a.suite}*_*_{a.side}.tsv"))):
        name = os.path.basename(f)
        if f != base_file and ("baselines_" in name or (not a.suite and name.startswith(("niche_", "fresh_")))):
            continue
        d = pd.read_csv(f, sep="\t")
        frames.append(d[["table", "split", "model", "r2", "rmse", "nonfinite"]])
    r = pd.concat(frames, ignore_index=True).drop_duplicates(["table", "split", "model"])
    r = r[r.split.isin(["iid1", "xfeat", "xy", "time", "xfeat_lo", "xy_lo"])]
    if a.models:
        keep = set(a.models.split(",")) | {"mean", "edge", "lightgbm"}
        r = r[r.model.isin(keep)]
    base = r[r.model == "mean"].set_index(["table", "split"])["rmse"]
    r = r.assign(rel=r["rmse"].to_numpy() / base.reindex(pd.MultiIndex.from_frame(r[["table", "split"]])).to_numpy())
    for split in ("iid1", "xfeat", "xy", "time", "xfeat_lo", "xy_lo"):
        k = r[r.split == split]
        rel = k.pivot(index="table", columns="model", values="rel")
        r2 = k.pivot(index="table", columns="model", values="r2")
        models = [m for m in rel.columns if m not in ("mean",)]
        no_edge = split in ("iid1", "time")
        full = rel.dropna(subset=[m for m in models if m != "edge" or not no_edge])
        print(f"\n== {split}: {len(full)} tables with every model ({len(rel)} in all)")
        rows = []
        for m in models:
            if m == "edge" and no_edge:
                continue
            s = full[m]
            lgb = int((s < full["lightgbm"]).sum()) if m != "lightgbm" else np.nan
            edge = int((s < full["edge"]).sum()) if "edge" in full and m != "edge" else np.nan
            bad = int(k[(k.model == m) & k.table.isin(full.index)]["nonfinite"].clip(lower=0).gt(0).sum())
            rows.append([m, s.median(), r2.loc[full.index, m].median(), lgb, edge, bad])
        out = pd.DataFrame(rows, columns=["model", "median_rel_rmse", "median_r2", "beats_lightgbm", "beats_edge",
                                          "tables_with_nonfinite"])
        print(out.sort_values("median_rel_rmse").to_string(index=False, float_format="%.4g"))


if __name__ == "__main__":
    main()
