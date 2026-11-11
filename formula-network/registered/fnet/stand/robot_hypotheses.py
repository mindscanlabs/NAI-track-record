"""The robot test's summary and hypotheses (docs/prereg/FNET_ROBOT.md): nMSE per joint, the mean over the 12
training combinations x 16 test trajectories, for NAI-fnet, tuned LightGBM and MLP 32x32 (each + the nominal model),
the nominal model alone, and the authors' four GP models from their published estimates on the same rows (checked:
their Y equals our tau_interp at every 10th row). C size and speed of the elbow models (combination 0).
    python -s -E robot_hypotheses.py --results RESULTS/robot_test_raw_residual_sub10
"""
import argparse
import csv
import os
import sys

import numpy as np

import robot_run as rr

B = "D:/Claude/nai-data/fnet/robot/baselines"
GP = {"with_NP_model_LK_GIP_sum": "LIP GP (paper)", "model_m_ind_GIP_with_friction": "GIP GP + friction",
      "with_linear_friction_model_LK_RBF_1_sc": "LSE GP", "model_m_ind_RBF": "RBF GP per joint"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    a = ap.parse_args()
    chk = {s: rr.traj(s) for s in rr.TEST}
    tab = {}          # (model, joint) -> list of nMSE over (comb, seed)
    # ours
    for model in ("fnet", "lightgbm_tuned", "mlp32"):
        for j in range(1, 8):
            for c in range(12):
                f = os.path.join(a.results, f"{model}__j{j}__comb{c:02d}.npz")
                if not os.path.exists(f):
                    continue
                z = np.load(f)
                assert list(z["seeds"]) == rr.TEST
                tab.setdefault((model, j), []).extend(list(z["nmse"]))
    # the nominal model alone
    for j in range(1, 8):
        tab[("nominal", j)] = [rr.nmse(chk[s][f"tau_interp_{j}"].to_numpy(), chk[s][f"tau_nom_{j}"].to_numpy()) for s in rr.TEST] * 12
    # the authors' GPs
    worst = 0.0
    for e in csv.DictReader(open(f"{B}/estimates_index.tsv"), delimiter="\t"):
        z = np.load(f"{B}/{e['file']}")
        s = int(e["seed"])
        y = np.stack([chk[s][f"tau_interp_{j}"].to_numpy() for j in range(1, 8)])
        if z["Y"].shape != y.shape:
            print("shape differs", e["file"], z["Y"].shape, y.shape, file=sys.stderr)
            continue
        worst = max(worst, float(np.max(np.abs(z["Y"] - y))))
        for j in range(1, 8):
            tab.setdefault((GP[e["model"]], j), []).append(rr.nmse(y[j - 1], z["Y_hat"][j - 1]))
    print(f"check: max |their Y - our tau_interp[::10]| = {worst:.3g}")
    names = ["fnet", "lightgbm_tuned", "mlp32", "nominal"] + list(GP.values())
    print("nMSE % (mean over combinations x test trajectories)".ljust(28), " ".join(f"j{j}".rjust(8) for j in range(1, 8)), "    mean  n(j4)")
    M = {}
    for n in names:
        row = [np.mean(tab[(n, j)]) if (n, j) in tab else np.nan for j in range(1, 8)]
        M[n] = row
        print(n.ljust(28), " ".join(f"{v:8.4f}" for v in row), f"{np.nanmean(row):8.4f}", len(tab.get((n, 4), [])))
    # C size and speed of the elbow models (combination 0)
    C = {}
    for model in ("fnet", "lightgbm_tuned", "mlp32"):
        f = os.path.join(a.results, f"{model}__j4__comb00.npz")
        if os.path.exists(f):
            z = np.load(f)
            if "c_bytes" in z.files:
                C[model] = (int(z["c_bytes"]), float(z["c_ns"]), float(z["c_maxdiff"]))
                print(f"C {model}: {C[model][0]} bytes, {C[model][1]:.1f} ns, max |C - model| {C[model][2]:.3g}")
    # hypotheses (thresholds as registered)
    f4, l4, m4, lip4 = M["fnet"][3], M["lightgbm_tuned"][3], M["mlp32"][3], M["LIP GP (paper)"][3]
    gipf = np.nanmean(M["GIP GP + friction"])
    print()
    print(f"H1 elbow: fnet {f4:.4f} % <= LIP GP {lip4:.4f} %: {'yes' if f4 <= lip4 else 'no'}")
    print(f"H2 elbow: fnet {f4:.4f} % <= 1.25 x tuned LightGBM {l4:.4f} % = {1.25 * l4:.4f} %: {'yes' if f4 <= 1.25 * l4 else 'no'}")
    print(f"H3 elbow: fnet {f4:.4f} % < MLP 32x32 {m4:.4f} %: {'yes' if f4 < m4 else 'no'}")
    if "fnet" in C and "lightgbm_tuned" in C:
        rb, rs = C["lightgbm_tuned"][0] / C["fnet"][0], C["lightgbm_tuned"][1] / C["fnet"][1]
        print(f"H4 elbow C: LightGBM / fnet size x{rb:.1f}, speed x{rs:.1f} (both >= 10), C = model {C['fnet'][2] == 0}: "
              f"{'yes' if rb >= 10 and rs >= 10 and C['fnet'][2] == 0 else 'no'}")
    wins = sum(1 for j in range(7) if M["fnet"][j] < M["LIP GP (paper)"][j])
    print(f"H5 all joints: fnet below LIP GP on {wins} of 7 joints (at least 5): {'yes' if wins >= 5 else 'no'}")
    print(f"(reported) mean over joints: fnet {np.nanmean(M['fnet']):.4f} %, LIP GP {np.nanmean(M['LIP GP (paper)']):.4f} %, "
          f"GIP GP + friction {gipf:.4f} %")


if __name__ == "__main__":
    main()
