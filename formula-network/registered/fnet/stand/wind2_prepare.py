"""Hill of Towie wind farm open dataset (RES on behalf of TRIG; Zenodo 10.5281/zenodo.22662930, version 2.1.0, CC BY
4.0), 21 Siemens SWT-2.3-VS-82 turbines (2300 kW), 10-minute SCADA -> per-turbine tables of normal operation for the
expected-power model of the second wind test (fnet/README.md 25; the formulation of docs/prereg/FNET_WIND.md).

Rules, fixed before any model was run on these data (the status and setpoint fields' distributions in 2018 were looked
at; no power or wind-power relation was):
- 10-minute rows (TimeStamp = end of the period); train = 2018, test = 2019; all 21 turbines (T01-T21);
- normal operation: in operation for the whole period (wtc_ScInOper_timeon = 600 s); no turbine, grid, environment
  or communication stop in it (wtc_ScTurSto, ScGrdSto, ScEnvSto, ScComSto timeon = 0); no curtailment or derating:
  the power setpoint at the rated 2300 kW at the end of this period and of the previous one (wtc_PowerRef_endvalue;
  in 2018 93 % of the rows are at 2300, the rest at discrete levels 1993, 2208, 2116, 100, 0 kW: a derating, not a
  value that follows the wind as at Penmanshiel); not stopped: power > 20 kW whenever the wind speed exceeds 4 m/s;
  every input and the power present;
- inputs (conditions of the wind only): wind speed from the active sensor (wtc_AcWindSp_mean, m/s), its standard
  deviation within the period (wtc_AcWindSp_stddev, m/s), sin and cos of the nacelle position (wtc_NacelPos_mean,
  turbine north; the wind direction field starts only in 2022-04), the ambient temperature (wtc_AmbieTmp_mean, deg
  C); target: active power (wtc_ActPower_mean, kW). The yaw misalignment of the Penmanshiel test has no field in
  these years, so there are five inputs instead of six.
Also kept (not inputs): the time.
    python -s -E wind2_prepare.py      # D:/Claude/nai-data/fnet/wind2/tables/Tnn_{train,test}.csv, MANIFEST.tsv
"""
import hashlib
import io
import os
import zipfile

import numpy as np
import pandas as pd

RAW = "D:/Claude/nai-data/fnet/wind2/raw"
OUT = "D:/Claude/nai-data/fnet/wind2/tables"
YEARS = {2018: "train", 2019: "test"}
STATION0 = 2304509                      # StationId = turbine number + 2304509 (the dataset's data dictionary)
FIELDS = {
    "tblSCTurbine": ["wtc_AcWindSp_mean", "wtc_AcWindSp_stddev", "wtc_NacelPos_mean", "wtc_PowerRef_endvalue"],
    "tblSCTurGrid": ["wtc_ActPower_mean"],
    "tblSCTurTemp": ["wtc_AmbieTmp_mean"],
    "tblSCTurFlag": ["wtc_ScInOper_timeon", "wtc_ScTurSto_timeon", "wtc_ScGrdSto_timeon", "wtc_ScEnvSto_timeon",
                     "wtc_ScComSto_timeon"],
}
INPUTS = ["ws", "ws_sd", "dir_sin", "dir_cos", "temp"]
RATED = 2300.0


def year_frame(year):
    z = zipfile.ZipFile(os.path.join(RAW, f"{year}.zip"))
    names = z.namelist()
    months = []
    for m in range(1, 13):
        d = None
        for table, cols in FIELDS.items():
            n = [x for x in names if x.rsplit("/", 1)[-1] == f"{table}_{year}_{m:02d}.csv"]
            if len(n) != 1:
                raise SystemExit(f"{year}: {table} {m}: {n}")
            t = pd.read_csv(io.BytesIO(z.read(n[0])), usecols=["TimeStamp", "StationId"] + cols)
            t = t.drop_duplicates(["TimeStamp", "StationId"])
            d = t if d is None else d.merge(t, on=["TimeStamp", "StationId"], how="inner")
        months.append(d)
    d = pd.concat(months, ignore_index=True)
    d["time"] = pd.to_datetime(d["TimeStamp"])
    return d.drop(columns=["TimeStamp"])


def clean(d):
    d = d.sort_values("time").copy()
    n0 = len(d)
    prev_ref = d["wtc_PowerRef_endvalue"].shift(1).where(d["time"].diff() == pd.Timedelta(minutes=10))
    ok = d["wtc_ScInOper_timeon"] == 600
    for c in ("wtc_ScTurSto_timeon", "wtc_ScGrdSto_timeon", "wtc_ScEnvSto_timeon", "wtc_ScComSto_timeon"):
        ok &= d[c] == 0
    ok &= (d["wtc_PowerRef_endvalue"] >= RATED) & (prev_ref >= RATED)
    d = d.rename(columns={"wtc_AcWindSp_mean": "ws", "wtc_AcWindSp_stddev": "ws_sd", "wtc_AmbieTmp_mean": "temp",
                          "wtc_ActPower_mean": "power"})
    ok &= ~((d["ws"] > 4) & (d["power"] <= 20))
    d = d[ok].copy()
    d["dir_sin"] = np.sin(np.radians(d["wtc_NacelPos_mean"]))
    d["dir_cos"] = np.cos(np.radians(d["wtc_NacelPos_mean"]))
    d = d.dropna(subset=INPUTS + ["power"])
    return d, n0


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for year, side in YEARS.items():
        d = year_frame(year)
        for k in range(1, 22):
            t, n0 = clean(d[d["StationId"] == STATION0 + k])
            path = f"{OUT}/T{k:02d}_{side}.csv"
            t[["time"] + INPUTS + ["power"]].to_csv(path, index=False, float_format="%.6g")
            h = hashlib.sha256(open(path, "rb").read()).hexdigest()
            rows.append((k, side, n0, len(t), t["temp"].min(), t["temp"].max(), h))
            print(f"T{k:02d} {side:5s} rows {n0:6d} -> {len(t):6d}  temp {t['temp'].min():5.1f}..{t['temp'].max():5.1f}  "
                  f"ws max {t['ws'].max():.1f}", flush=True)
    with open(f"{OUT}/MANIFEST.tsv", "w", newline="\n") as f:
        f.write("turbine\tside\trows_raw\trows\ttemp_min\ttemp_max\tsha256\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


if __name__ == "__main__":
    main()
