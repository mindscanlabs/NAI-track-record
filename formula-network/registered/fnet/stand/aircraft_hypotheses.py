"""The aircraft test's summary and hypotheses (docs/prereg/FNET_AIRCRAFT.md) from aircraft_run.py's results.
    python -s -E aircraft_hypotheses.py --results RESULTS/aircraft_test
"""
import argparse
import os

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--results", required=True)
a = ap.parse_args()
M = ["fnet", "table", "lightgbm_tuned", "mlp32"]
T = ["CLWALL", "CDWALL", "CMWALL"]
R = {(m, t): np.load(os.path.join(a.results, f"{m}__{t}.npz")) for m in M for t in T}
for t in T:
    unit, u = (1e4, " counts") if t == "CDWALL" else (1.0, "")
    print(t)
    for m in M:
        z = R[(m, t)]
        cs = f"C {int(z['c_bytes'])} B, {float(z['c_ns']):.0f} ns" if "c_bytes" in z.files else f"table of {int(z['table_values'])} values"
        print(f"  {m:16s} inside RMSE {float(z['rmse_inside']) * unit:9.4g}{u} ({float(z['rmse_inside']) / float(z['sd_inside']):.3f} sd)"
              f"   edge RMSE {float(z['rmse_edge']) * unit:9.4g}{u} ({float(z['rmse_edge']) / float(z['sd_edge']):.3f} sd)   {cs}")
g = lambda m, t, k: float(R[(m, t)][f"rmse_{k}"])
print()
print(f"H1 CD beyond the edge: fnet {g('fnet', 'CDWALL', 'edge') * 1e4:.1f} counts < table {g('table', 'CDWALL', 'edge') * 1e4:.1f}: "
      f"{'yes' if g('fnet', 'CDWALL', 'edge') < g('table', 'CDWALL', 'edge') else 'no'}")
print(f"H2 CD beyond the edge: fnet {g('fnet', 'CDWALL', 'edge') * 1e4:.1f} counts <= tuned LightGBM {g('lightgbm_tuned', 'CDWALL', 'edge') * 1e4:.1f}: "
      f"{'yes' if g('fnet', 'CDWALL', 'edge') <= g('lightgbm_tuned', 'CDWALL', 'edge') else 'no'}")
print(f"H3 CL beyond the edge: fnet {g('fnet', 'CLWALL', 'edge'):.4f} <= tuned LightGBM {g('lightgbm_tuned', 'CLWALL', 'edge'):.4f}: "
      f"{'yes' if g('fnet', 'CLWALL', 'edge') <= g('lightgbm_tuned', 'CLWALL', 'edge') else 'no'}")
print(f"H4 CD inside: fnet {g('fnet', 'CDWALL', 'inside') * 1e4:.1f} counts <= 1.15 x tuned LightGBM {g('lightgbm_tuned', 'CDWALL', 'inside') * 1e4:.1f}: "
      f"{'yes' if g('fnet', 'CDWALL', 'inside') <= 1.15 * g('lightgbm_tuned', 'CDWALL', 'inside') else 'no'}")
ratios = [int(R[('lightgbm_tuned', t)]["c_bytes"]) / int(R[('fnet', t)]["c_bytes"]) for t in T]
same = all(float(R[('fnet', t)]["c_maxdiff"]) == 0 for t in T)
print(f"H5 C: LightGBM / fnet size {', '.join(f'x{r:.1f}' for r in ratios)} (each >= 10), C = model {same}: "
      f"{'yes' if min(ratios) >= 10 and same else 'no'}")
