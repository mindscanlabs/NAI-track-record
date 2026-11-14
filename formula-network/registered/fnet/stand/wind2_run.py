"""The formula network as the expected-power model of a wind turbine, second wind test (Hill of Towie T01-T21;
wind2_prepare.py; a copy of wind_run.py of the Penmanshiel test with this farm's tables, inputs and rating): power
from the wind's conditions; one model per turbine.

  --side dev   2018 only: fit on 2018-01-01 .. 2018-09-30, check on 2018-10-01 .. 2018-12-31;
  --side test  fit on 2018, check on 2019; only with --registered PATH.
Fit rows: every --step-th row (default 2). Models: fnet (nai_cli --net, release settings); iec (the industry's power
curve, IEC 61400-12-1 style: wind speed normalised to the fit period's mean air density, rho ~ 1/T at constant
pressure, v_n = v (T_ref / T)^(1/3); mean power in 0.5 m/s bins; linear interpolation between bin centres, the end
bins' values beyond them); lightgbm_tuned (20 settings, 3-fold check grouped by calendar week); mlp32.
Metrics per turbine and pooled: RMSE (kW) and NRMSE (% of the rated 2300 kW), MAE, and the energy error (sum of
predicted over sum of measured power, minus 1, %).
    python -s -E wind_run.py --side dev --models fnet,iec,lightgbm_tuned,mlp32
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

D = "D:/Claude/nai-data/fnet/wind2/tables"
CLI = "C:/msys64/home/ceo/nai/fnet/build/v14b/nai_cli_v14b.exe"
TURBINES = list(range(1, 22))
INPUTS = ["ws", "ws_sd", "dir_sin", "dir_cos", "temp"]
TEMP = INPUTS.index("temp")
RATED = 2300.0


class IEC:
    def fit(self, X, y):
        self.tref = np.mean(X[:, TEMP] + 273.15)
        v = self.vn(X)
        edges = np.arange(0, 30.5, 0.5)
        k = np.digitize(v, edges) - 1
        self.c, self.p = [], []
        for b in range(len(edges) - 1):
            m = k == b
            if m.sum() >= 3:
                self.c.append(v[m].mean()); self.p.append(y[m].mean())
        self.c, self.p = np.array(self.c), np.array(self.p)
        return self

    def vn(self, X):
        return X[:, 0] * (self.tref / (X[:, TEMP] + 273.15)) ** (1 / 3)

    def predict(self, X):
        return np.interp(self.vn(X), self.c, self.p)


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
    ap.add_argument("--turbines", default=",".join(map(str, TURBINES)))
    ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--seconds", type=float, default=120)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--cli", default=CLI)
    a = ap.parse_args()
    if a.side == "test" and not (a.registered and os.path.exists(a.registered)):
        sys.exit("the test part runs only after registration: --registered PATH")
    out = os.path.join(RESULTS, f"wind2_{a.side}" + ("" if a.step == 2 else f"_step{a.step}"))
    os.makedirs(out, exist_ok=True)
    for t in [int(x) for x in a.turbines.split(",")]:
        tr = pd.read_csv(f"{D}/T{t:02d}_train.csv", parse_dates=["time"])
        if a.side == "dev":
            fit, chk = tr[tr.time < "2018-10-01"], tr[tr.time >= "2018-10-01"]
        else:
            fit, chk = tr, pd.read_csv(f"{D}/T{t:02d}_test.csv", parse_dates=["time"])
        fit = fit.iloc[::a.step]
        X, y = fit[INPUTS].to_numpy(), fit.power.to_numpy()
        Xc, yc = chk[INPUTS].to_numpy(), chk.power.to_numpy()
        for model in a.models.split(","):
            tag = f"{model}__T{t:02d}"
            res = os.path.join(out, tag + ".npz")
            if os.path.exists(res):
                print("done before:", tag)
                continue
            base = os.path.join(out, tag)
            t0 = time.time()
            ctext = None
            if model in ("fnet", "fnet_res"):
                # fnet_res: the IEC curve (fitted on the same rows) is the nominal model, the network learns its error
                trf, pf, prf, cfile = base + ".train.txt", base + ".points.txt", base + ".pred.txt", base + ".c"
                if model == "fnet_res":
                    iec = IEC().fit(X, y)
                    fx, cx = fit[INPUTS].copy(), chk[INPUTS].copy()
                    fx["iec"], cx["iec"] = iec.predict(X), iec.predict(Xc)
                    write_table(trf, fx, y - fx["iec"].to_numpy())
                    write_table(pf, cx)
                else:
                    write_table(trf, fit[INPUTS], y)
                    write_table(pf, chk[INPUTS])
                cmd = [a.cli, "--net", "--data", trf, "--predict", pf, prf, "--export-c", cfile, "--seconds",
                       str(a.seconds), "--threads", str(a.threads), "--seed", "1"]
                p = subprocess.run(cmd, capture_output=True, timeout=10 * a.seconds + 1200)
                open(base + ".log", "wb").write(p.stdout + p.stderr)
                pred = np.array([float(v) for v in open(prf).read().split()])
                for f in (trf, pf, prf):
                    os.remove(f)
                ctext, name = open(cfile).read(), "fnet_predict"
                if model == "fnet_res":
                    own = pred.copy()
                    pred = pred + cx["iec"].to_numpy()
            else:
                if model == "iec":
                    m = IEC().fit(X, y)
                elif model == "lightgbm_tuned":
                    from robot_run import lgbm_c
                    week = fit.time.dt.isocalendar().week.to_numpy()
                    m = tuned_lgbm(X, y, week)
                    ctext, name = lgbm_c(m), "score"
                elif model == "mlp32":
                    from competitors import mlp, mlp_c
                    m = mlp(32).fit(X, y)
                    ctext, name = mlp_c(m, X.shape[1]), "mlp_predict"
                else:
                    sys.exit("unknown model " + model)
                pred = m.predict(Xc)
            secs = time.time() - t0
            extra = {}
            if ctext:
                from size import compile_and_measure
                cd = base + "_c"
                os.makedirs(cd, exist_ok=True)
                sel = np.arange(0, len(yc), max(1, len(yc) // 5000))
                if model == "fnet_res":   # the network's own C on its inputs (the curve is a 60-entry table beside it)
                    nb, ns, cpred = compile_and_measure(cd, ctext, name, cx.to_numpy()[sel], 200)
                    extra = dict(c_bytes=nb, c_ns=ns, c_maxdiff=float(np.nanmax(np.abs(cpred - own[sel]))))
                else:
                    nb, ns, cpred = compile_and_measure(cd, ctext, name, Xc[sel], 200)
                    extra = dict(c_bytes=nb, c_ns=ns, c_maxdiff=float(np.nanmax(np.abs(cpred - pred[sel]))))
            e = pred - yc
            rmse, mae = float(np.sqrt(np.mean(e ** 2))), float(np.mean(np.abs(e)))
            energy = float(pred.sum() / yc.sum() - 1)
            np.savez(res, pred=pred, y=yc, time=chk.time.astype("int64").to_numpy(), rmse=rmse, mae=mae, energy=energy,
                     secs=secs, **extra)
            print(f"T{t:02d} {model:15s} RMSE {rmse:7.1f} kW (NRMSE {100 * rmse / RATED:5.2f} %)  MAE {mae:6.1f}  "
                  f"energy {100 * energy:+6.2f} %  {secs:.0f} s  " + " ".join(f"{k}={v:.4g}" for k, v in extra.items()),
                  flush=True)


if __name__ == "__main__":
    import threading
    sys.setrecursionlimit(200000)
    threading.stack_size(256 * 1024 * 1024 - 4096)
    th = threading.Thread(target=main)
    th.start()
    th.join()
