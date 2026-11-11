"""Penmanshiel wind farm SCADA (Cubico Sustainable Investments; Zenodo 10.5281/zenodo.16807304, CC BY 4.0), turbines
WT11-WT15 (Senvion MM82, 2050 kW) -> per-turbine tables of normal operation for a power model.

Rules, fixed before any model was run:
- 10-minute rows; train = 2018-04-05 to 2018-12-31 (the pitch signal starts on 2018-04-05), test = 2019;
- normal operation: Data Availability = 1; Available Capacity for Production at least 2000 kW or missing (no
  curtailment, no derating); not stopped: power > 20 kW whenever the wind speed exceeds 4 m/s. (Turbine Power
  setpoint is not a curtailment flag: it is the 10-minute mean of a reference that follows the wind, median 1185 kW
  in 2018; a first draft of this rule used it and kept 17 % of the rows; found before any model was run.)
  every input and the power present;
- inputs (conditions of the wind only, not the turbine's own response, so that a fault shows as a gap between the
  measured and the predicted power): wind speed (m/s), its standard deviation within the 10 minutes (m/s), the yaw
  misalignment (Vane position 1+2, deg), sin and cos of the wind direction, the nacelle ambient temperature (deg C);
  target: Power (kW).
Also kept for the site and the checks (not inputs): rotor speed, pitch, time.
    python -s -E wind_prepare.py      # D:/Claude/nai-data/fnet/wind/tables/WTnn_{train,test}.csv, MANIFEST.tsv
"""
import hashlib
import io
import os
import re
import zipfile

import numpy as np
import pandas as pd

RAW = "D:/Claude/nai-data/fnet/wind/raw"
OUT = "D:/Claude/nai-data/fnet/wind/tables"
ZIPS = {2018: "Penmanshiel_SCADA_2018_WT11-15_3116.zip", 2019: "Penmanshiel_SCADA_2019_WT11-15_3117.zip"}
TURBINES = [11, 12, 13, 14, 15]
COLS = {
    "Power (kW)": "power", "Wind speed (m/s)": "ws", "Wind speed, Standard deviation (m/s)": "ws_sd",
    "Wind direction (°)": "dir", "Vane position 1+2 (°)": "yaw_mis", "Nacelle ambient temperature (°C)": "temp",
    "Rotor speed (RPM)": "rpm", "Blade angle (pitch position) A (°)": "pitch", "Data Availability": "avail",
    "Turbine Power setpoint (kW)": "setpoint", "Available Capacity for Production (kW)": "capacity",
}
INPUTS = ["ws", "ws_sd", "yaw_mis", "dir_sin", "dir_cos", "temp"]


def read_member(z, name):
    raw = z.read(name).decode("utf-8", "replace").splitlines()
    k = next(i for i, l in enumerate(raw) if l.startswith("# Date and time"))
    head = raw[k][2:]
    d = pd.read_csv(io.StringIO("\n".join([head] + raw[k + 1:])), low_memory=False)
    d = d.rename(columns={"Date and time": "time"})
    missing = [c for c in COLS if c not in d.columns]
    if missing:
        raise SystemExit(f"{name}: missing columns {missing}")
    d = d[["time"] + list(COLS)].rename(columns=COLS)
    d["time"] = pd.to_datetime(d["time"])
    return d


def clean(d):
    n0 = len(d)
    ok = (d["avail"] == 1)
    ok &= d["capacity"].isna() | (d["capacity"] >= 2000)
    ok &= ~((d["ws"] > 4) & (d["power"] <= 20))
    d = d[ok].copy()
    d["dir_sin"] = np.sin(np.radians(d["dir"]))
    d["dir_cos"] = np.cos(np.radians(d["dir"]))
    d = d.dropna(subset=INPUTS + ["power"])
    return d, n0


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for year, zname in ZIPS.items():
        z = zipfile.ZipFile(os.path.join(RAW, zname))
        for t in TURBINES:
            m = [n for n in z.namelist() if re.search(rf"Turbine_Data_Penmanshiel_{t:02d}_", n)]
            if len(m) != 1:
                raise SystemExit(f"{zname}: turbine {t}: {m}")
            d = read_member(z, m[0])
            if year == 2018:
                d = d[d["time"] >= "2018-04-05"]
            d, n0 = clean(d)
            side = "train" if year == 2018 else "test"
            path = f"{OUT}/WT{t:02d}_{side}.csv"
            d[["time"] + INPUTS + ["power", "rpm", "pitch"]].to_csv(path, index=False, float_format="%.6g")
            h = hashlib.sha256(open(path, "rb").read()).hexdigest()
            rows.append((t, side, n0, len(d), d["temp"].min(), d["temp"].max(), h))
            print(f"WT{t:02d} {side:5s} rows {n0:6d} -> {len(d):6d}  temp {d['temp'].min():5.1f}..{d['temp'].max():5.1f}  "
                  f"ws max {d['ws'].max():.1f}")
    with open(f"{OUT}/MANIFEST.tsv", "w", newline="\n") as f:
        f.write("turbine\tside\trows_raw\trows\ttemp_min\ttemp_max\tsha256\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


if __name__ == "__main__":
    main()
