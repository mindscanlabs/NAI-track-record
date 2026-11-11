"""The wind test's summary and hypotheses (docs/prereg/FNET_WIND.md) from wind_run.py's results.
    python -s -E wind_hypotheses.py --results RESULTS/wind_test
"""
import argparse
import os

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--results", required=True)
a = ap.parse_args()
T = [11, 12, 13, 14, 15]
M = ["fnet_res", "iec", "lightgbm_tuned", "mlp32"]
R = {m: [np.load(os.path.join(a.results, f"{m}__WT{t:02d}.npz")) for t in T] for m in M}
print(f"{'model':16s} " + " ".join(f"WT{t:02d} NRMSE %".rjust(15) for t in T) + "   mean   |energy| %   C bytes / ns (WT11)")
S = {}
for m in M:
    nr = [100 * float(z["rmse"]) / 2050 for z in R[m]]
    en = [100 * abs(float(z["energy"])) for z in R[m]]
    S[m] = (np.mean(nr), np.mean(en), [float(z["rmse"]) for z in R[m]])
    c = R[m][0]
    cs = f"{int(c['c_bytes'])} / {float(c['c_ns']):.0f}" if "c_bytes" in c.files else "-"
    print(f"{m:16s} " + " ".join(f"{v:15.3f}" for v in nr) + f" {np.mean(nr):6.3f} {np.mean(en):10.2f}   {cs}")
f, iec, lgb, mlp = S["fnet_res"][0], S["iec"][0], S["lightgbm_tuned"][0], S["mlp32"][0]
print()
print(f"H1 fnet mean NRMSE {f:.3f} % < IEC power curve {iec:.3f} %: {'yes' if f < iec else 'no'}")
print(f"H2 fnet mean NRMSE {f:.3f} % <= 1.15 x tuned LightGBM {lgb:.3f} % = {1.15 * lgb:.3f} %: {'yes' if f <= 1.15 * lgb else 'no'}")
print(f"H3 fnet mean NRMSE {f:.3f} % < MLP 32x32 {mlp:.3f} %: {'yes' if f < mlp else 'no'}")
rb = [int(R["lightgbm_tuned"][k]["c_bytes"]) / int(R["fnet_res"][k]["c_bytes"]) for k in range(5)]
rs = [float(R["lightgbm_tuned"][k]["c_ns"]) / float(R["fnet_res"][k]["c_ns"]) for k in range(5)]
same = all(float(z["c_maxdiff"]) == 0 for z in R["fnet_res"])
print(f"H4 LightGBM / fnet C, median over turbines: size x{np.median(rb):.1f}, time x{np.median(rs):.1f} (both >= 10), "
      f"C = model on every turbine {same}: {'yes' if np.median(rb) >= 10 and np.median(rs) >= 10 and same else 'no'}")
print(f"H5 mean |energy error| fnet {S['fnet_res'][1]:.2f} % < IEC {S['iec'][1]:.2f} %: {'yes' if S['fnet_res'][1] < S['iec'][1] else 'no'}")
print(f"(reported) mean |energy error|: LightGBM {S['lightgbm_tuned'][1]:.2f} %, MLP {S['mlp32'][1]:.2f} %")
