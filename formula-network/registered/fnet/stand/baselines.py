"""Step 2 (P0): baseline models on the prepared tables and splits.

Runs the WORKING part only; the test part needs a registration file (--registered PATH), so it cannot be
looked at by accident. Results are appended to RESULTS/baselines_<side>.tsv; finished (table, split, model)
rows are skipped on a rerun.

Models (defaults unless "_tuned", the same thread count for all): ridge (degree-2 polynomial up to 30 features, else
linear; alpha by internal CV), MLP (64, 64; early stopping), LightGBM, XGBoost, CatBoost, EBM, FFX (model of
the Pareto front with the best error on 20 % of the training rows), and two references: the training mean
and, for the extrapolation splits, the mean of the training rows at the edge (top 5 % along the split axis; bottom 5 %
for the lower-tail splits xfeat_lo, xy_lo).
Size = length of the pickled model; prediction time = batch time on the test rows per row.
"""
import argparse
import csv
import os
import pickle
import sys
import time
import warnings

import numpy as np
import pandas as pd

from common import load_splits, REPO_DATA, RESULTS, SPLITS, TABLES, metrics

warnings.filterwarnings("ignore")
THREADS = 4
MODELS = ["mean", "edge", "ridge", "mlp", "lightgbm", "xgboost", "catboost", "ebm", "ffx", "lightgbm_tuned",
          "catboost_tuned"]


def tuned(name, split):
    """Random search over 20 settings, 3-fold check inside the training rows (by time for the split "time")."""
    from scipy.stats import loguniform
    from sklearn.model_selection import KFold, RandomizedSearchCV, TimeSeriesSplit
    cv = TimeSeriesSplit(n_splits=3) if split == "time" else KFold(n_splits=3, shuffle=True, random_state=0)
    if name == "lightgbm_tuned":
        import lightgbm
        est = lightgbm.LGBMRegressor(n_jobs=THREADS, verbose=-1, random_state=0)
        dist = {"num_leaves": [7, 15, 31, 63, 127], "learning_rate": loguniform(0.01, 0.3),
                "n_estimators": [100, 300, 1000], "min_child_samples": [5, 10, 20, 50],
                "subsample": [0.7, 1.0], "subsample_freq": [1], "colsample_bytree": [0.6, 0.8, 1.0],
                "reg_lambda": loguniform(1e-3, 10)}
    else:
        import catboost
        est = catboost.CatBoostRegressor(thread_count=THREADS, verbose=0, allow_writing_files=False, random_seed=0)
        dist = {"depth": [4, 6, 8], "learning_rate": loguniform(0.01, 0.3), "iterations": [300, 1000],
                "l2_leaf_reg": loguniform(1, 10)}
    return RandomizedSearchCV(est, dist, n_iter=20, cv=cv, scoring="neg_mean_squared_error", random_state=0, n_jobs=1)


def make(name, p, split=""):
    if name.endswith("_tuned"):
        return tuned(name, split)
    from sklearn.compose import TransformedTargetRegressor
    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import PolynomialFeatures, StandardScaler
    if name == "ridge":
        steps = [StandardScaler()] + ([PolynomialFeatures(2), StandardScaler()] if p <= 30 else [])
        return make_pipeline(*steps, RidgeCV(alphas=np.logspace(-4, 4, 17)))
    if name == "mlp":
        from sklearn.neural_network import MLPRegressor
        m = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 64), early_stopping=True,
                                                          max_iter=500, random_state=0))
        return TransformedTargetRegressor(regressor=m, transformer=StandardScaler())
    if name == "lightgbm":
        import lightgbm
        return lightgbm.LGBMRegressor(n_jobs=THREADS, verbose=-1, random_state=0)
    if name == "xgboost":
        import xgboost
        return xgboost.XGBRegressor(n_jobs=THREADS, random_state=0)
    if name == "catboost":
        import catboost
        return catboost.CatBoostRegressor(thread_count=THREADS, verbose=0, allow_writing_files=False,
                                          random_seed=0)
    if name == "ebm":
        from interpret.glassbox import ExplainableBoostingRegressor
        return ExplainableBoostingRegressor(n_jobs=THREADS, random_state=0)
    if name == "ffx":
        return FFX()
    raise ValueError(name)


class FFX:
    def fit(self, X, y):
        import ffx
        k = int(0.8 * len(y))
        p = np.random.default_rng(0).permutation(len(y))
        a, b = p[:k], p[k:]
        models = ffx.run(X[a], y[a], X[b], y[b], [f"x{i}" for i in range(X.shape[1])])
        errs = [np.mean((m.simulate(X[b]) - y[b]) ** 2) for m in models]
        self.model = models[int(np.argmin(errs))]
        return self

    def predict(self, X):
        return self.model.simulate(X)


class Const:
    def __init__(self, v):
        self.v = float(v)

    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.full(len(X), self.v)


def edge_value(Xtr, ytr, split, info):
    if not split.startswith("x"):
        return None
    v = ytr if info["on"] == "target" else Xtr[info["on"]].to_numpy()
    if split.endswith("_lo"):                   # a lower tail: the edge is the bottom of the training rows
        return ytr[v <= np.quantile(v, 0.05)].mean()
    return ytr[v >= np.quantile(v, 0.95)].mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", default="work", choices=["work", "test"])
    ap.add_argument("--assignment", default="assignment.tsv", help="niche_assignment.tsv for the niche suite")
    ap.add_argument("--registered", help="registration file; required for --side test")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--tables", default="", help="comma-separated table keys (default: all of the side)")
    ap.add_argument("--splits", default="", help="comma-separated splits (default: all of each table)")
    a = ap.parse_args()
    if a.side == "test" and not (a.registered and os.path.exists(a.registered)):
        sys.exit("the test part runs only after registration: --registered PATH")
    import json
    with open(os.path.join(REPO_DATA, a.assignment)) as f:
        keys = [r["table"] for r in csv.DictReader(f, delimiter="\t") if r["side"] == a.side]
    if a.tables:
        keys = [k for k in keys if k in set(a.tables.split(","))]
    models = a.models.split(",")
    os.makedirs(RESULTS, exist_ok=True)
    suite = a.assignment.replace("assignment.tsv", "")   # "niche_", "fresh_" or "" (the general suite)
    out_path = os.path.join(RESULTS, f"{suite}baselines_{a.side}.tsv")
    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            done = {(r["table"], r["split"], r["model"]) for r in csv.DictReader(f, delimiter="\t")}
    new = not os.path.exists(out_path)
    out = open(out_path, "a", newline="")
    w = csv.writer(out, delimiter="\t", lineterminator="\n")
    if new:
        w.writerow(["table", "split", "model", "r2", "rmse", "nonfinite", "fit_s", "predict_us_per_row",
                    "model_bytes", "n_train", "n_test"])
    for key in keys:
        fn = key.replace(":", "__")
        t = pd.read_csv(os.path.join(TABLES, fn + ".csv"))
        sp, info = load_splits(fn)
        X, y = t.drop(columns=["target"]), t["target"].to_numpy()
        for split in [x for x in sorted(info) if not a.splits or x in a.splits.split(",")]:
            tr, te = sp[f"{split}_train"], sp[f"{split}_test"]
            for m in models:
                if (key, split, m) in done or (m == "edge" and not split.startswith("x")):
                    continue
                t0 = time.time()
                try:
                    if m == "mean":
                        model = Const(y[tr].mean())
                    elif m == "edge":
                        model = Const(edge_value(X.iloc[tr], y[tr], split, info[split]))
                    else:
                        model = make(m, X.shape[1], split).fit(X.iloc[tr].to_numpy(), y[tr])
                    fit_s = time.time() - t0
                    t1 = time.time()
                    p = np.asarray(model.predict(X.iloc[te].to_numpy()), dtype=float).ravel()
                    pred_us = (time.time() - t1) / len(te) * 1e6
                    r2, rmse, bad = metrics(y[te], p, y[tr].mean())
                    try:
                        size = len(pickle.dumps(model))
                    except Exception:
                        size = -1
                    row = [key, split, m, f"{r2:.6g}", f"{rmse:.6g}", bad, f"{fit_s:.3f}", f"{pred_us:.3f}", size,
                           len(tr), len(te)]
                except Exception as e:
                    row = [key, split, m, "nan", "nan", -1, f"{time.time() - t0:.3f}", "nan", -1, len(tr), len(te)]
                    print(f"  FAILED {key} {split} {m}: {type(e).__name__}: {e}", flush=True)
                w.writerow(row)
                out.flush()
            print(f"{key} {split} done", flush=True)
    out.close()


if __name__ == "__main__":
    main()
