"""Electric Motor Temperature (Kirchgaessner, Wallscheid, Boecker, Paderborn University; Kaggle v3, CC BY-SA 4.0;
DOI 10.34740/KAGGLE/DSV/2161054) -> per-profile feature tables for the rotor (permanent magnet) temperature.

Features, fixed before any model was run, after Kirchgaessner et al., IEEE TPEL 36(7) 2021 (the features of their
table II and the spans their search Omega found for the rotor): 7 measured signals (ambient, coolant, u_d, u_q, i_d,
i_q, motor_speed) and 5 derived ones (u_s = |u|, i_s = |i|, S_el = 1.5 u_s i_s, i_s * omega, S_el * omega, with
omega = motor_speed), each as is and as exponentially weighted moving averages (pandas ewm, adjust=True) with spans
500, 2161, 4000, 8895 samples (2 Hz), computed per profile from its first sample: 60 inputs. Target: pm (deg C).
Torque is left out (derived from the set points; the papers do not use it).

Sides: test = profiles 60, 62, 74 (the authors' generalization set for this version, Thermal Neural Networks, EAAI
2023); dev check = 58, 65, 72 (their validation and test profiles of the earlier, 140-hour version); the rest train.
    python -s -E motor_prepare.py      # D:/Claude/nai-data/fnet/motor/tables/profile_NN.npz, MANIFEST.tsv
"""
import hashlib
import io
import os
import zipfile

import numpy as np
import pandas as pd

RAW = "D:/Claude/nai-data/fnet/motor/raw/electric-motor-temperature-v3.zip"
OUT = "D:/Claude/nai-data/fnet/motor/tables"
SPANS = [500, 2161, 4000, 8895]
BASE = ["ambient", "coolant", "u_d", "u_q", "i_d", "i_q", "motor_speed"]
TEST = [60, 62, 74]
DEV = [58, 65, 72]


def features(p):
    f = p[BASE].copy()
    f["u_s"] = np.hypot(p["u_d"], p["u_q"])
    f["i_s"] = np.hypot(p["i_d"], p["i_q"])
    f["S_el"] = 1.5 * f["u_s"] * f["i_s"]
    f["i_s_w"] = f["i_s"] * p["motor_speed"]
    f["S_el_w"] = f["S_el"] * p["motor_speed"]
    cols = list(f.columns)
    for s in SPANS:
        e = f[cols].ewm(span=s, adjust=True).mean()
        e.columns = [f"{c}_ew{s}" for c in cols]
        f = pd.concat([f, e], axis=1)
    return f


def main():
    os.makedirs(OUT, exist_ok=True)
    z = zipfile.ZipFile(RAW)
    d = pd.read_csv(io.BytesIO(z.read("measures_v2.csv")))
    rows = []
    for pid, p in d.groupby("profile_id", sort=True):
        p = p.reset_index(drop=True)
        f = features(p)
        side = "test" if pid in TEST else "dev" if pid in DEV else "train"
        path = f"{OUT}/profile_{int(pid):02d}.npz"
        np.savez(path, X=f.to_numpy(np.float64), y=p["pm"].to_numpy(np.float64), cols=np.array(list(f.columns), dtype=str),
                 coolant=p["coolant"].to_numpy(), speed=p["motor_speed"].to_numpy(), torque=p["torque"].to_numpy(),
                 i_s=f["i_s"].to_numpy(), stator=p["stator_winding"].to_numpy(),
                 stator_yoke=p["stator_yoke"].to_numpy(), stator_tooth=p["stator_tooth"].to_numpy())
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        rows.append((int(pid), side, len(p), len(p) / 7200, h))
        print(f"profile {pid:2d} {side:5s} rows {len(p):6d} ({len(p) / 7200:.2f} h)")
    with open(f"{OUT}/MANIFEST.tsv", "w", newline="\n") as fh:
        fh.write("profile\tside\trows\thours\tsha256\n")
        for r in rows:
            fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]:.3f}\t{r[4]}\n")
    n = {s: sum(r[2] for r in rows if r[1] == s) for s in ("train", "dev", "test")}
    print("rows by side", n, "features", len(features(d.head(10)).columns))


if __name__ == "__main__":
    main()
