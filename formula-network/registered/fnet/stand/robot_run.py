"""The formula network on the real Panda arm (Zenodo 12516500), the authors' protocol (LIP4RobotInverseDynamics,
RealData/PANDA/config): a model per joint, inputs from q, dq, ddq of all 7 joints, target tau_interp of the joint;
combination c trains on the training seeds TRAIN[c], TRAIN[c + 1] (every 10th row, downsampling_data_load = 10),
and is checked on the 16 test trajectories (every 10th row). The archive holds one training file per seed
(num_sin_50); the authors' configs list two (num_sin_50 and num_sin_100).

  --side dev   training seeds only: combination c is checked on the training seeds it does not use;
  --side test  the 16 test seeds; only with --registered PATH (one look).

Formulations (fnet/README.md, section 3):
  --features raw    q, dq, ddq of the 7 joints (21 inputs)
  --features trig   the same and sin q, cos q of each joint (35)
  --target full     the model gives tau_interp
  --target residual the model gives tau_interp - tau_nom (the nominal rigid-body model in the archive,
                    M(q) ddq + c(q, dq) + g(q), robot_nominal.py); the prediction is tau_nom + model
Models: fnet (nai_cli --net, release settings), lightgbm_tuned (baselines.tuned), mlp32 (competitors.mlp(32)).
Writes RESULTS/robot_<side>_<features>_<target>_<rows>/<model>__j<joint>__comb<c>.npz (predictions on every
check trajectory, nMSE per trajectory) and, for the first combination given, the C size and speed
(size.compile_and_measure).
    python -s -E robot_run.py --side dev --joints 4 --combs 0 --models fnet --features trig --target residual
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

D = "D:/Claude/nai-data/fnet/robot/tables"
CLI = "C:/msys64/home/ceo/nai/bench/results/v26/nai_cli_v26.exe"
TRAIN = [2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 16, 18]
TEST = [21, 22, 23, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]
RAW = [f"{k}_{j}" for k in ("q", "dq", "ddq") for j in range(1, 8)]
TRIG = [f"{k}_q_{j}" for k in ("sin", "cos") for j in range(1, 8)]
STEP = 10


def traj(seed, step=STEP):
    t = pd.read_csv(f"{D}/panda_seed{seed:02d}_nom.csv")
    for j in range(1, 8):
        t[f"sin_q_{j}"] = np.sin(t[f"q_{j}"])
        t[f"cos_q_{j}"] = np.cos(t[f"q_{j}"])
    return t.iloc[::step].reset_index(drop=True)


def lgbm_c(model):
    """A LightGBM regressor as C (double): one function a tree, nested ifs, then their sum. m2cgen builds one
    expression over all trees and runs out of stack at 1000 trees; this walks one tree at a time."""
    dump = model.booster_.dump_model()
    out = ["#include <math.h>"]

    def node(n, ind):
        if "leaf_value" in n:
            return f"{ind}return {float(n['leaf_value']):.17g};\n"
        if n.get("decision_type", "<=") != "<=":
            raise ValueError("unsupported split " + str(n.get("decision_type")))
        f, thr = n["split_feature"], float(n["threshold"])
        miss = "|| isnan(x[%d])" % f if n.get("default_left", True) else ""
        return (f"{ind}if (x[{f}] <= {thr:.17g} {miss}) {{\n" + node(n["left_child"], ind + "    ")
                + f"{ind}}} else {{\n" + node(n["right_child"], ind + "    ") + f"{ind}}}\n")

    trees = dump["tree_info"]
    for k, t in enumerate(trees):
        out.append(f"static double tree{k}(const double* x) {{\n" + node(t["tree_structure"], "    ") + "}")
    body = "".join(f"    s += tree{k}(x);\n" for k in range(len(trees)))
    out.append("double score(const double* x) {\n    double s = 0.0;\n" + body + "    return s;\n}")
    return "\n".join(out) + "\n"


def nmse(y, p):
    return 100.0 * float(np.mean((y - p) ** 2) / np.var(y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", choices=["dev", "test"], required=True)
    ap.add_argument("--registered")
    ap.add_argument("--joints", default="4")
    ap.add_argument("--combs", default="0")
    ap.add_argument("--models", default="fnet")
    ap.add_argument("--features", choices=["raw", "trig"], default="raw")
    ap.add_argument("--target", choices=["full", "residual"], default="full")
    ap.add_argument("--rows", choices=["sub10", "all"], default="sub10", help="training rows: every 10th or all")
    ap.add_argument("--seconds", type=float, default=120)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--cli", default=CLI)
    ap.add_argument("--no-c", action="store_true", help="skip the C size and speed")
    a = ap.parse_args()
    if a.side == "test" and not (a.registered and os.path.exists(a.registered)):
        sys.exit("the test part runs only after registration: --registered PATH")
    feats = RAW + (TRIG if a.features == "trig" else [])
    out = os.path.join(RESULTS, f"robot_{a.side}_{a.features}_{a.target}_{a.rows}")
    os.makedirs(out, exist_ok=True)
    combs = [int(x) for x in a.combs.split(",")]
    for c in combs:
        tr_seeds = TRAIN[c:c + 2]
        chk_seeds = TEST if a.side == "test" else [s for s in TRAIN if s not in tr_seeds]
        tr = pd.concat([traj(s, STEP if a.rows == "sub10" else 1) for s in tr_seeds], ignore_index=True)
        chk = [traj(s) for s in chk_seeds]
        P = pd.concat([t[feats] for t in chk], ignore_index=True)
        lens = [len(t) for t in chk]
        cut = np.cumsum([0] + lens)
        for j in [int(x) for x in a.joints.split(",")]:
            ycol, ncol = f"tau_interp_{j}", f"tau_nom_{j}"
            ytr = tr[ycol].to_numpy() - (tr[ncol].to_numpy() if a.target == "residual" else 0.0)
            back = np.concatenate([t[ncol].to_numpy() for t in chk]) if a.target == "residual" else 0.0
            for model in a.models.split(","):
                tag = f"{model}__j{j}__comb{c:02d}"
                res = os.path.join(out, tag + ".npz")
                if os.path.exists(res):
                    print("done before:", tag)
                    continue
                base = os.path.join(out, tag)
                t0 = time.time()
                ctext, predict_name = None, None
                if model == "fnet":
                    trf, pf, prf, cfile = base + ".train.txt", base + ".points.txt", base + ".pred.txt", base + ".c"
                    write_table(trf, tr[feats], ytr)
                    write_table(pf, P)
                    cmd = [a.cli, "--net", "--data", trf, "--predict", pf, prf, "--export-c", cfile, "--seconds",
                           str(a.seconds), "--threads", str(a.threads), "--seed", "1"]
                    p = subprocess.run(cmd, capture_output=True, timeout=6 * a.seconds + 600)
                    open(base + ".log", "wb").write(p.stdout + p.stderr)
                    own = np.array([float(v) for v in open(prf).read().split()])
                    for f in (trf, pf, prf):
                        os.remove(f)
                    ctext = open(cfile).read() if os.path.exists(cfile) else None
                    predict_name = "fnet_predict"
                else:
                    X = tr[feats].to_numpy()
                    if model == "lightgbm_tuned":
                        from baselines import tuned
                        m = tuned("lightgbm_tuned", "iid1").fit(X, ytr).best_estimator_
                        ctext, predict_name = lgbm_c(m), "score"
                    elif model == "mlp32":
                        from competitors import mlp, mlp_c
                        m = mlp(32).fit(X, ytr)
                        ctext, predict_name = mlp_c(m, X.shape[1]), "mlp_predict"
                    else:
                        sys.exit("unknown model " + model)
                    own = m.predict(P.to_numpy())
                secs = time.time() - t0
                pred = own + back
                per = [nmse(chk[k][ycol].to_numpy(), pred[cut[k]:cut[k + 1]]) for k in range(len(chk))]
                extra = {}
                if ctext and not a.no_c and c == combs[0]:
                    from size import compile_and_measure
                    d = base + "_c"
                    os.makedirs(d, exist_ok=True)
                    nb, ns, cpred = compile_and_measure(d, ctext, predict_name, P.to_numpy(dtype=float), 200)
                    extra = dict(c_bytes=nb, c_ns=ns, c_maxdiff=float(np.nanmax(np.abs(cpred - own))))
                np.savez(res, pred=pred, lens=np.array(lens), seeds=np.array(chk_seeds), nmse=np.array(per),
                         secs=secs, **extra)
                print(f"{os.path.basename(out)} {tag}: nMSE mean {np.mean(per):.3f} % median {np.median(per):.3f} %"
                      f"  {secs:.0f} s  " + " ".join(f"{k}={v:.4g}" for k, v in extra.items()), flush=True)


if __name__ == "__main__":
    # m2cgen walks 1000 trees recursively: a deep Python stack in a thread with a big C stack
    import threading
    sys.setrecursionlimit(200000)
    threading.stack_size(256 * 1024 * 1024 - 4096)
    th = threading.Thread(target=main)
    th.start()
    th.join()
