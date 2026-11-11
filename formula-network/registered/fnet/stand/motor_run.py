"""The formula network as a virtual rotor-temperature sensor of a traction motor (Electric Motor Temperature,
Paderborn; motor_prepare.py). Inputs: the 60 features of motor_prepare.py (signals and their EWMAs); target pm.

  --side dev   train on the train profiles, check on the dev profiles 58, 65, 72;
  --side test  train on train + dev profiles, check on the test profiles 60, 62, 74; only with --registered PATH.
Training rows: every --step-th sample of each profile (the EWMAs are computed at the full rate first); checks use
every sample. Models: fnet (nai_cli --net, release settings), ols (least squares on the same features), lightgbm_tuned
(random search over 20 settings, 3-fold check grouped by profile), mlp32 (competitors.mlp(32)). Metrics: MSE (K^2)
and the largest absolute error (K) over all check samples, and per profile. C size and speed of each model
(size.compile_and_measure) on the check points.
    python -s -E motor_run.py --side dev --models fnet,ols,lightgbm_tuned,mlp32 --step 60
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

D = "D:/Claude/nai-data/fnet/motor/tables"
CLI = "C:/msys64/home/ceo/nai/bench/results/v26/nai_cli_v26.exe"


SPANS = [500, 2161, 4000, 8895]


def load(side, features="base"):
    """base: the 60 features of motor_prepare.py; stator: also the three measured stator temperatures (yoke, tooth,
    winding: thermistors a production inverter has) and the EWMAs of the winding temperature (same spans): 67."""
    m = pd.read_csv(f"{D}/MANIFEST.tsv", sep="\t")
    out = []
    cols = list(np.load(f"{D}/profile_02.npz")["cols"])
    if features == "stator":
        cols = cols + ["stator_yoke", "stator_tooth", "stator_winding"] + [f"stator_winding_ew{s}" for s in SPANS]
    for pid in m[m.side == side].profile:
        z = np.load(f"{D}/profile_{pid:02d}.npz", allow_pickle=False)
        X = z["X"]
        if features == "stator":
            w = pd.Series(z["stator"])
            ew = np.column_stack([w.ewm(span=s, adjust=True).mean().to_numpy() for s in SPANS])
            X = np.column_stack([X, z["stator_yoke"], z["stator_tooth"], z["stator"], ew])
        out.append((pid, X, z["y"]))
    return out, cols


# compact: the stator temperatures, coolant, ambient, speed, current, electric power, and the EWMAs of the current,
# the speed and the two loss-like products (i_s * omega, S_el * omega): 24 inputs
COMPACT = ["stator_yoke", "stator_tooth", "stator_winding", "coolant", "ambient", "motor_speed", "i_s", "S_el"] + [
    f"{c}_ew{s}" for c in ("i_s", "motor_speed", "i_s_w", "S_el_w") for s in SPANS]


def select(data, cols, names):
    idx = [cols.index(n) for n in names]
    return [(pid, X[:, idx], y) for pid, X, y in data], list(names)


def ols_c(model, V):
    fmt = lambda a: ", ".join("%.17g" % v for v in np.ravel(a))
    return f"""static const double w[{V}] = {{ {fmt(model.coef_)} }};
double ols_predict(const double x[]) {{
    double s = {float(model.intercept_):.17g};
    for (int i = 0; i < {V}; ++i) s += w[i] * x[i];
    return s;
}}
"""


def tuned_lgbm(X, y, groups):
    import lightgbm
    from scipy.stats import loguniform
    from sklearn.model_selection import GroupKFold, RandomizedSearchCV
    est = lightgbm.LGBMRegressor(n_jobs=4, verbose=-1, random_state=0)
    dist = {"num_leaves": [7, 15, 31, 63, 127], "learning_rate": loguniform(0.01, 0.3),
            "n_estimators": [100, 300, 1000], "min_child_samples": [5, 10, 20, 50],
            "subsample": [0.7, 1.0], "subsample_freq": [1], "colsample_bytree": [0.6, 0.8, 1.0],
            "reg_lambda": loguniform(1e-3, 10)}
    s = RandomizedSearchCV(est, dist, n_iter=20, cv=GroupKFold(n_splits=3), scoring="neg_mean_squared_error",
                           random_state=0, n_jobs=1)
    return s.fit(X, y, groups=groups).best_estimator_


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", choices=["dev", "test"], required=True)
    ap.add_argument("--registered")
    ap.add_argument("--models", default="fnet")
    ap.add_argument("--step", type=int, default=60)
    ap.add_argument("--seconds", type=float, default=120)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--cli", default=CLI)
    ap.add_argument("--tag", default="")
    ap.add_argument("--features", choices=["base", "stator", "compact"], default="base")
    a = ap.parse_args()
    if a.side == "test" and not (a.registered and os.path.exists(a.registered)):
        sys.exit("the test part runs only after registration: --registered PATH")
    kind = "stator" if a.features == "compact" else a.features
    train, cols = load("train", kind)
    dev, _ = load("dev", kind)
    test, _ = load("test", kind)
    if a.features == "compact":
        (train, _), (dev, _), (test, cols) = select(train, cols, COMPACT), select(dev, cols, COMPACT), select(test, cols, COMPACT)
    fit_on, check = (train, dev) if a.side == "dev" else (train + dev, test)
    Xtr = np.vstack([X[::a.step] for _, X, _ in fit_on])
    ytr = np.concatenate([y[::a.step] for _, _, y in fit_on])
    gtr = np.concatenate([np.full(len(y[::a.step]), pid) for pid, _, y in fit_on])
    Xc = np.vstack([X for _, X, _ in check])
    yc = np.concatenate([y for _, _, y in check])
    lens = [len(y) for _, _, y in check]
    cut = np.cumsum([0] + lens)
    out = os.path.join(RESULTS, f"motor_{a.side}_{a.features}_step{a.step}{a.tag}")
    os.makedirs(out, exist_ok=True)
    print(f"train rows {len(ytr)} (step {a.step}), check rows {len(yc)}, inputs {len(cols)}", flush=True)
    for model in a.models.split(","):
        res = os.path.join(out, model + ".npz")
        if os.path.exists(res):
            print("done before:", model)
            continue
        base = os.path.join(out, model)
        t0 = time.time()
        if model == "fnet":
            trf, pf, prf, cfile = base + ".train.txt", base + ".points.txt", base + ".pred.txt", base + ".c"
            write_table(trf, pd.DataFrame(Xtr, columns=cols), ytr)
            write_table(pf, pd.DataFrame(Xc, columns=cols))
            cmd = [a.cli, "--net", "--data", trf, "--predict", pf, prf, "--export-c", cfile, "--seconds",
                   str(a.seconds), "--threads", str(a.threads), "--seed", "1"]
            p = subprocess.run(cmd, capture_output=True, timeout=10 * a.seconds + 1800)
            open(base + ".log", "wb").write(p.stdout + p.stderr)
            pred = np.array([float(v) for v in open(prf).read().split()])
            for f in (trf, pf, prf):
                os.remove(f)
            ctext, name = open(cfile).read(), "fnet_predict"
        else:
            if model == "ols":
                # ridge on standardised features (plain least squares is ill-conditioned here: the features span 1e-2..1e8
                # and are nearly collinear); written back to the raw features for the C code
                from sklearn.linear_model import RidgeCV
                mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-12
                r = RidgeCV(alphas=np.logspace(-6, 3, 19)).fit((Xtr - mu) / sd, ytr)
                class Lin:
                    coef_ = r.coef_ / sd
                    intercept_ = float(r.intercept_ - np.sum(r.coef_ * mu / sd))
                    def predict(self, X): return X @ self.coef_ + self.intercept_
                m = Lin()
                ctext, name = ols_c(m, Xtr.shape[1]), "ols_predict"
            elif model == "lightgbm_tuned":
                from robot_run import lgbm_c
                m = tuned_lgbm(Xtr, ytr, gtr)
                ctext, name = lgbm_c(m), "score"
            elif model == "mlp32":
                from competitors import mlp, mlp_c
                m = mlp(32).fit(Xtr, ytr)
                ctext, name = mlp_c(m, Xtr.shape[1]), "mlp_predict"
            else:
                sys.exit("unknown model " + model)
            pred = m.predict(Xc)
        secs = time.time() - t0
        e = pred - yc
        warm = np.concatenate([np.arange(cut[k] + 1200, cut[k + 1]) for k in range(len(lens))])   # after 10 min
        per = [(int(pid), float(np.mean(e[cut[k]:cut[k + 1]] ** 2)), float(np.max(np.abs(e[cut[k]:cut[k + 1]]))))
               for k, (pid, _, _) in enumerate(check)]
        from size import compile_and_measure
        d = base + "_c"
        os.makedirs(d, exist_ok=True)
        sel = np.arange(0, len(yc), max(1, len(yc) // 5000))
        nb, ns, cpred = compile_and_measure(d, ctext, name, Xc[sel], 200)
        np.savez(res, pred=pred, y=yc, lens=np.array(lens), pids=np.array([p for p, _, _ in check]),
                 mse=float(np.mean(e ** 2)), maxerr=float(np.max(np.abs(e))), maxerr_warm=float(np.max(np.abs(e[warm]))),
                 per=np.array(per), secs=secs,
                 c_bytes=nb, c_ns=ns, c_maxdiff=float(np.nanmax(np.abs(cpred - pred[sel]))))
        print(f"{model:15s} MSE {np.mean(e ** 2):7.3f} K^2  max {np.max(np.abs(e)):6.2f} K (after 10 min {np.max(np.abs(e[warm])):5.2f})  "
              + "  ".join(f"[{p}: {m2:.2f}/{mx:.1f}]" for p, m2, mx in per)
              + f"  {secs:.0f} s  C {nb} B {ns:.0f} ns", flush=True)


if __name__ == "__main__":
    import threading
    sys.setrecursionlimit(200000)
    threading.stack_size(256 * 1024 * 1024 - 4096)
    th = threading.Thread(target=main)
    th.start()
    th.join()
