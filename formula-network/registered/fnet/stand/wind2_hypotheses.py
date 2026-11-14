"""The second wind test's summary and hypotheses (docs/prereg/FNET_WIND2.md) from wind2_run.py's results; the same five
hypotheses as the Penmanshiel test (wind_hypotheses.py), over the 21 Hill of Towie turbines.
    python -s -E wind2_hypotheses.py --results RESULTS/wind2_test
"""
import argparse
import os

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--results", required=True)
a = ap.parse_args()
T = list(range(1, 22))
RATED = 2300.0
M = ["fnet_res", "iec", "lightgbm_tuned", "mlp32"]
R = {m: [np.load(os.path.join(a.results, f"{m}__T{t:02d}.npz")) for t in T] for m in M}
S = {}
print(f"{'turbine':8s} " + " ".join(f"{m + ' NRMSE %':>22s} {'energy %':>9s}" for m in M))
for k, t in enumerate(T):
    print(f"T{t:02d}      " + " ".join(f"{100 * float(R[m][k]['rmse']) / RATED:22.3f} {100 * float(R[m][k]['energy']):+9.2f}"
                                       for m in M))
for m in M:
    nr = [100 * float(z["rmse"]) / RATED for z in R[m]]
    en = [100 * abs(float(z["energy"])) for z in R[m]]
    S[m] = (np.mean(nr), np.mean(en))
    c = R[m][0]
    cs = f"{int(c['c_bytes'])} B / {float(c['c_ns']):.0f} ns (T01)" if "c_bytes" in c.files else ""
    print(f"{m:16s} mean NRMSE {np.mean(nr):6.3f} %  mean |energy| {np.mean(en):5.2f} %  {cs}")
f, iec, lgb, mlp = S["fnet_res"][0], S["iec"][0], S["lightgbm_tuned"][0], S["mlp32"][0]
print()
print(f"H1 fnet mean NRMSE {f:.3f} % < IEC power curve {iec:.3f} %: {'yes' if f < iec else 'no'}")
print(f"H2 fnet mean NRMSE {f:.3f} % <= 1.15 x tuned LightGBM {lgb:.3f} % = {1.15 * lgb:.3f} %: {'yes' if f <= 1.15 * lgb else 'no'}")
print(f"H3 fnet mean NRMSE {f:.3f} % < MLP 32x32 {mlp:.3f} %: {'yes' if f < mlp else 'no'}")
rb = [int(R["lightgbm_tuned"][k]["c_bytes"]) / int(R["fnet_res"][k]["c_bytes"]) for k in range(len(T))]
rs = [float(R["lightgbm_tuned"][k]["c_ns"]) / float(R["fnet_res"][k]["c_ns"]) for k in range(len(T))]
same = all(float(z["c_maxdiff"]) == 0 for z in R["fnet_res"])
print(f"H4 LightGBM / fnet C, median over turbines: size x{np.median(rb):.1f}, time x{np.median(rs):.1f} (both >= 10), "
      f"C = model on every turbine {same}: {'yes' if np.median(rb) >= 10 and np.median(rs) >= 10 and same else 'no'}")
print(f"H5 mean |energy error| fnet {S['fnet_res'][1]:.2f} % < IEC {S['iec'][1]:.2f} %: {'yes' if S['fnet_res'][1] < S['iec'][1] else 'no'}")
print(f"(reported) mean |energy error|: LightGBM {S['lightgbm_tuned'][1]:.2f} %, MLP {S['mlp32'][1]:.2f} %")
