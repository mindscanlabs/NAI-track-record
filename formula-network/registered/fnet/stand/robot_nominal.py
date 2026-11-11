"""The nominal rigid-body model in the archive (dynamics_components: M, c, g per sample) against the measured
tau_interp: nMSE of tau - (M ddq + c + g) per joint on the training seeds, and a CSV column per joint with the
nominal torque (tau_nom_j), written next to the trajectory tables (every row).
    python -I robot_nominal.py
"""
import io
import re
import zipfile

import numpy as np
import pandas as pd

import robot_prepare as rp

D = "D:/Claude/nai-data/fnet/robot/tables"


def main():
    z = zipfile.ZipFile(rp.ZIP)
    pat = re.compile(r"panda7dof_num_sin_(\d+)_seed_(\d+)_as_filtered_fcut4\.0_dynamics_components\.pkl$")
    rows = []
    for n in sorted(z.namelist()):
        m = pat.search(n)
        if not m:
            continue
        seed = int(m.group(2))
        obj = rp.Restricted(io.BytesIO(z.read(n))).load()
        if isinstance(obj, dict):
            M, c, g = obj["M"], obj["c"], obj["g"]
        else:
            M, c, g = obj[0], obj[1], obj[2]
        M, c, g = np.asarray(M), np.asarray(c), np.asarray(g)
        t = pd.read_csv(f"{D}/panda_seed{seed:02d}.csv")
        N = len(t)
        ddq = t[[f"ddq_{j}" for j in range(1, 8)]].to_numpy()
        if M.shape[-1] != N and M.shape[0] == N:
            M = np.transpose(M, (1, 2, 0))
        if c.shape[0] != N:
            c, g = c.T, g.T
        if M.shape[-1] != N:
            print("shape mismatch", seed, M.shape, c.shape, g.shape, N)
            continue
        nom = np.einsum("ijn,nj->ni", M, ddq) + c + g
        tau = t[[f"tau_interp_{j}" for j in range(1, 8)]].to_numpy()
        e = 100 * np.mean((tau - nom) ** 2, axis=0) / np.var(tau, axis=0)
        eg = 100 * np.mean((tau - g) ** 2, axis=0) / np.var(tau, axis=0)
        rows.append((seed, e, eg))
        for j in range(7):
            t[f"tau_nom_{j + 1}"] = nom[:, j]
        t.to_csv(f"{D}/panda_seed{seed:02d}_nom.csv", index=False, float_format="%.17g")
    for seed, e, eg in rows:
        print(f"seed {seed:2d} nominal nMSE %: " + " ".join(f"{x:7.2f}" for x in e) + " | gravity only j4 " + f"{eg[3]:.2f}")
    print("mean nominal:", " ".join(f"{x:7.2f}" for x in np.mean([r[1] for r in rows], axis=0)))


if __name__ == "__main__":
    main()
