"""The motor test's summary and hypotheses (docs/prereg/FNET_MOTOR.md) from motor_run.py's results.
    python -s -E motor_hypotheses.py --results RESULTS/motor_test_stator_step60
"""
import argparse
import os

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--results", required=True)
a = ap.parse_args()
R = {}
for m in ("fnet", "mlp32", "ols", "lightgbm_tuned"):
    f = os.path.join(a.results, m + ".npz")
    if os.path.exists(f):
        R[m] = np.load(f)
print(f"{'model':16s} {'MSE K^2':>9s} {'max K':>7s} {'max K after 10 min':>19s} {'C bytes':>9s} {'C ns':>8s}  per profile (MSE / max)")
for m, z in R.items():
    print(f"{m:16s} {float(z['mse']):9.3f} {float(z['maxerr']):7.2f} {float(z['maxerr_warm']):19.2f} {int(z['c_bytes']):9d} "
          f"{float(z['c_ns']):8.1f}  " + "  ".join(f"[{int(p)}: {m2:.2f} / {mx:.1f}]" for p, m2, mx in z["per"]))
f, mlp, lgb, ols = (float(R[k]["mse"]) for k in ("fnet", "mlp32", "lightgbm_tuned", "ols"))
fw, mw = float(R["fnet"]["maxerr_warm"]), float(R["mlp32"]["maxerr_warm"])
print()
print(f"H1 fnet MSE {f:.3f} <= 1.15 x MLP 32x32 {mlp:.3f} = {1.15 * mlp:.3f}: {'yes' if f <= 1.15 * mlp else 'no'}")
print(f"H2 fnet MSE {f:.3f} <= 0.5 x tuned LightGBM {lgb:.3f} = {0.5 * lgb:.3f}: {'yes' if f <= 0.5 * lgb else 'no'}")
print(f"H3 fnet MSE {f:.3f} < ridge {ols:.3f}: {'yes' if f < ols else 'no'}")
print(f"H4 fnet max error after 10 min {fw:.2f} K <= 1.25 x MLP's {mw:.2f} = {1.25 * mw:.2f}: {'yes' if fw <= 1.25 * mw else 'no'}")
fb, lb, fd = int(R["fnet"]["c_bytes"]), int(R["lightgbm_tuned"]["c_bytes"]), float(R["fnet"]["c_maxdiff"])
print(f"H5 fnet C {fb} B < LightGBM C {lb} B, and C = model (max diff {fd:.3g}): {'yes' if fb < lb and fd == 0 else 'no'}")
print("(context, not comparable: Thermal Neural Network on the same test profiles without stator inputs, rotor only:"
      " MSE 4.34 K^2, max 6.02 K; Kirchgaessner et al., EAAI 2023, fig. 9)")
