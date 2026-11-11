"""The formula network as an aerodynamic model of a transport aircraft (NASA CRM, NTF Test 197; aircraft_prepare.py):
CL, CD and CM from the corrected angle of attack, Mach, Reynolds number, dynamic pressure and tail incidence.

  --side dev   train runs only: dev_edge = the training runs at nominal Mach 0.85 (beyond the rest), dev_inside =
               every 4th of the other training runs; the model trains on the remaining runs;
  --side test  train on all training runs, check on test_inside and test_edge; only with --registered PATH.
Models: fnet (nai_cli --net, release settings); table (a look-up table as in flight software: for each Reynolds
number and tail incidence of the training data, linear interpolation over (alpha, Mach) of the measured points,
nearest measured point outside them); lightgbm_tuned (20 settings, 3-fold check grouped by run); mlp32.
Metrics per target and check: RMSE, RMSE / sd of the check values; CD also in drag counts (1e-4).
    python -s -E aircraft_run.py --side dev --models fnet,table,lightgbm_tuned,mlp32
"""
import argparse
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from common import RESULTS
from nai_ref import write_table

TABLE = "D:/Claude/nai-data/fnet/aircraft/tables/crm_wbt.csv"
CLI = "C:/msys64/home/ceo/nai/bench/results/v26/nai_cli_v26.exe"
INPUTS = ["AWALL", "MWALL", "CREYN", "QINFFT", "CONFT"]
TARGETS = ["CLWALL", "CDWALL", "CMWALL"]


def lookup_table(tr, te, target):
    """Linear interpolation over (alpha, Mach) within the training points of the same Reynolds group and tail
    incidence; the nearest such point where the interpolation is undefined (outside their hull)."""
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
    key = lambda d: list(zip(d.CREYN.round(0), d.CONFT))
    out = np.full(len(te), np.nan)
    ktr, kte = np.array(key(tr), dtype=object), key(te)
    groups = {}
    for i, k in enumerate(kte):
        groups.setdefault(k, []).append(i)
    for k, idx in groups.items():
        m = np.array([kk == k for kk in map(tuple, ktr)])
        if m.sum() < 4:   # no table for this pair: the nearest point of any pair
            m = np.ones(len(tr), bool)
        P = tr.loc[m, ["AWALL", "MWALL"]].to_numpy() * [1, 100]     # Mach scaled: 0.01 Mach ~ 1 deg
        y = tr.loc[m, target].to_numpy()
        Q = te.iloc[idx][["AWALL", "MWALL"]].to_numpy() * [1, 100]
        lin = LinearNDInterpolator(P, y)(Q)
        near = NearestNDInterpolator(P, y)(Q)
        out[idx] = np.where(np.isfinite(lin), lin, near)
    return out


def tuned_lgbm(X, y, groups):
    import lightgbm
    from scipy.stats import loguniform
    from sklearn.model_selection import GroupKFold, RandomizedSearchCV
    est = lightgbm.LGBMRegressor(n_jobs=4, verbose=-1, random_state=0)
    dist = {"num_leaves": [7, 15, 31, 63], "learning_rate": loguniform(0.01, 0.3), "n_estimators": [100, 300, 1000],
            "min_child_samples": [3, 5, 10, 20], "subsample": [0.7, 1.0], "subsample_freq": [1],
            "colsample_bytree": [0.6, 0.8, 1.0], "reg_lambda": loguniform(1e-3, 10)}
    s = RandomizedSearchCV(est, dist, n_iter=20, cv=GroupKFold(n_splits=3), scoring="neg_mean_squared_error",
                           random_state=0, n_jobs=1)
    return s.fit(X, y, groups=groups).best_estimator_


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", choices=["dev", "test"], required=True)
    ap.add_argument("--registered")
    ap.add_argument("--models", default="fnet")
    ap.add_argument("--seconds", type=float, default=120)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--cli", default=CLI)
    a = ap.parse_args()
    if a.side == "test" and not (a.registered and os.path.exists(a.registered)):
        sys.exit("the test part runs only after registration: --registered PATH")
    d = pd.read_csv(TABLE)
    if a.side == "dev":
        t = d[d.side == "train"].copy()
        edge_runs = set(t[t.mach_nom >= 0.85].RUN)
        other = sorted(set(t.RUN) - edge_runs)
        inside_runs = set(other[3::4])
        t["side"] = ["check_edge" if r in edge_runs else "check_inside" if r in inside_runs else "fit" for r in t.RUN]
        fit, checks = t[t.side == "fit"], {"inside": t[t.side == "check_inside"], "edge": t[t.side == "check_edge"]}
    else:
        fit = d[d.side == "train"]
        checks = {"inside": d[d.side == "test_inside"], "edge": d[d.side == "test_edge"]}
    out = os.path.join(RESULTS, f"aircraft_{a.side}")
    os.makedirs(out, exist_ok=True)
    allc = pd.concat(list(checks.values()), ignore_index=True)
    lens = [len(c) for c in checks.values()]
    print(f"fit points {len(fit)} ({fit.RUN.nunique()} runs); checks " + ", ".join(f"{k} {len(v)}" for k, v in checks.items()), flush=True)
    for target in TARGETS:
        for model in a.models.split(","):
            tag = f"{model}__{target}"
            res = os.path.join(out, tag + ".npz")
            if os.path.exists(res):
                print("done before:", tag)
                continue
            base = os.path.join(out, tag)
            t0 = time.time()
            extra = {}
            if model == "fnet":
                trf, pf, prf, cfile = base + ".train.txt", base + ".points.txt", base + ".pred.txt", base + ".c"
                write_table(trf, fit[INPUTS], fit[target].to_numpy())
                write_table(pf, allc[INPUTS])
                cmd = [a.cli, "--net", "--data", trf, "--predict", pf, prf, "--export-c", cfile, "--seconds",
                       str(a.seconds), "--threads", str(a.threads), "--seed", "1"]
                p = subprocess.run(cmd, capture_output=True, timeout=10 * a.seconds + 900)
                open(base + ".log", "wb").write(p.stdout + p.stderr)
                pred = np.array([float(v) for v in open(prf).read().split()])
                for f in (trf, pf, prf):
                    os.remove(f)
                ctext, name = open(cfile).read(), "fnet_predict"
            elif model == "table":
                pred = lookup_table(fit, allc, target)
                ctext = None
                extra["table_values"] = len(fit)
            else:
                X = fit[INPUTS].to_numpy()
                if model == "lightgbm_tuned":
                    from robot_run import lgbm_c
                    m = tuned_lgbm(X, fit[target].to_numpy(), fit.RUN.to_numpy())
                    ctext, name = lgbm_c(m), "score"
                elif model == "mlp32":
                    from competitors import mlp, mlp_c
                    m = mlp(32).fit(X, fit[target].to_numpy())
                    ctext, name = mlp_c(m, X.shape[1]), "mlp_predict"
                else:
                    sys.exit("unknown model " + model)
                pred = m.predict(allc[INPUTS].to_numpy())
            secs = time.time() - t0
            if ctext:
                from size import compile_and_measure
                cd = base + "_c"
                os.makedirs(cd, exist_ok=True)
                nb, ns, cpred = compile_and_measure(cd, ctext, name, allc[INPUTS].to_numpy(dtype=float), 500)
                extra.update(c_bytes=nb, c_ns=ns, c_maxdiff=float(np.nanmax(np.abs(cpred - pred))))
            y = allc[target].to_numpy()
            cut = np.cumsum([0] + lens)
            stats = {}
            for k, (name_c, _) in enumerate(checks.items()):
                e = pred[cut[k]:cut[k + 1]] - y[cut[k]:cut[k + 1]]
                stats[name_c] = (float(np.sqrt(np.mean(e ** 2))), float(np.std(y[cut[k]:cut[k + 1]])))
            np.savez(res, pred=pred, y=y, lens=np.array(lens), names=np.array(list(checks), dtype=str), secs=secs,
                     **{f"rmse_{k}": v[0] for k, v in stats.items()}, **{f"sd_{k}": v[1] for k, v in stats.items()}, **extra)
            unit = 1e4 if target == "CDWALL" else 1.0
            print(f"{target} {model:15s} " + "  ".join(
                f"{k}: RMSE {v[0] * unit:8.4g}{' cts' if unit > 1 else ''} ({v[0] / v[1]:.3f} sd)" for k, v in stats.items())
                + f"  {secs:.0f} s  " + " ".join(f"{k}={v:.4g}" for k, v in extra.items()), flush=True)


if __name__ == "__main__":
    import threading
    sys.setrecursionlimit(200000)
    threading.stack_size(256 * 1024 * 1024 - 4096)
    th = threading.Thread(target=main)
    th.start()
    th.join()
