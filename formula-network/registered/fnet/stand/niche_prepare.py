"""Niche suite (fnet/README.md §8): tables of smooth engineering and physical dependencies.

Rules fixed before any model is run on these tables (§8, §8.1, user decisions 02.11.2026):
- not inputs: other outputs of the same system (energy_efficiency cooling_load, sulfur y2, CHF and Olympus
  only their named target), columns derived from the target (grid_stability stabf, Synchronous Machine dIf),
  columns derived from other inputs (Synchronous Machine e = 1 − PF), identifiers, names, SMILES, another
  model's prediction (ESOL predicted), set and class labels;
- cleaning as in prepare.py (missing, categorical ≤ 10 levels, constants, ≤ 20 000 rows, names);
- families: CHF (Zhao, KAERI), QSAR (aquatic, bioconcentration, fish), Olympus (Suzuki, HPLC); the rest alone;
- lottery over the families, seed 20261102, half to the working part;
- static tables: splits iid1..3, xfeat, xy as in prepare.py; time series: one split "time" — the first 75 % of
  the rows in time order train, the last 25 % test.
"""
import csv
import gzip
import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pandas as pd

from common import DATA, REPO_DATA, sha256
from prepare import clean, make_splits

NICHE = os.path.join(DATA, "niche")
RAW = os.path.join(NICHE, "raw")
TABLES = os.path.join(DATA, "tables")
SPLITS = os.path.join(DATA, "splits")
SEED = 20261102


def raw(name):
    return os.path.join(RAW, name)


# ---------------------------------------------------------------- static sources: (frame, target)

def ccpp():
    with zipfile.ZipFile(raw("ccpp.zip")) as z:
        return pd.read_excel(z.open("CCPP/Folds5x2_pp.xlsx"), sheet_name="Sheet1"), "PE"


def yacht():
    cols = ["LCB", "prismatic", "length_displacement", "beam_draught", "length_beam", "froude", "resistance"]
    return pd.read_csv(raw("x_yacht/yacht_hydrodynamics.data"), sep=r"\s+", names=cols), "resistance"


def syncmachine():
    t = pd.read_csv(raw("x_syncmachine/synchronous machine.csv"), sep=";", decimal=",")
    return t.drop(columns=["e", "dIf"]), "If"


def qsar_aquatic():
    cols = ["TPSA", "SAacc", "H050", "MLOGP", "RDCHI", "GATS1p", "nN", "C040", "LC50"]
    return pd.read_csv(raw("x_qsar_aquatic/qsar_aquatic_toxicity.csv"), sep=";", names=cols), "LC50"


def qsar_bcf():
    t = pd.read_csv(raw("x_qsar_bcf/Grisoni_et_al_2016_EnvInt88.csv"), encoding="utf-8-sig")
    return t.drop(columns=["CAS", "SMILES", "Set", "Class"]), "logBCF"


def autompg():
    cols = ["mpg", "cylinders", "displacement", "horsepower", "weight", "acceleration", "model_year", "origin", "name"]
    t = pd.read_csv(raw("x_autompg/auto-mpg.data"), sep=r"\s+", names=cols, na_values="?", quotechar='"')
    t["origin"] = t["origin"].astype(int).astype(str)          # 1, 2, 3: a category
    return t.drop(columns=["name"]), "mpg"


def nikuradse():
    with gzip.open(raw("nikuradse_1.tsv.gz"), "rt") as f:
        return pd.read_csv(f, sep="\t"), "target"


def galaxy():
    with gzip.open(raw("galaxy.tsv.gz"), "rt") as f:
        return pd.read_csv(f, sep="\t"), "target"


def esol():
    t = pd.read_csv(raw("esol.csv"))
    t = t.drop(columns=["Compound ID", "ESOL predicted log solubility in mols per litre", "smiles"])
    return t, "measured log solubility in mols per litre"


def chf_zhao():
    t = pd.read_csv(raw("chf_zhao.csv"), encoding="utf-8-sig")
    return t.drop(columns=["id", "author"]), "chf_exp [MW/m2]"


def chf_kaeri():
    # HeatFlux is the CHF; Power = HeatFlux × heated area (from the target), Area, Perimeter, MassFlow and
    # InletEnthalpy follow from other inputs; TestID, Source, Fluid and the axial profile are not inputs.
    keep = ["Diameter", "Length", "Pressure", "MassFlux", "EquilibriumQuality", "InletTemperature", "HeatFlux"]
    rows = [{c.tag: c.text for c in e} for e in ET.parse(raw("chf_kaeri_uniform.xml")).getroot()]
    return pd.DataFrame(rows)[keep], "HeatFlux"


def cfd_wavy():
    t = pd.read_csv(raw("x_cfd/ML_dataset_longform.csv"))
    return t.drop(columns=["case_uid", "raw_row_id", "geometry_id", "DelP_Pa"]), "Nuavg"


# ---------------------------------------------------------------- time series: rows in time order

def airquality():
    t = pd.read_csv(raw("x_aq/AirQualityUCI.csv"), sep=";", decimal=",").dropna(axis=1, how="all")
    t = t.replace(-200, np.nan)
    keep = ["PT08.S1(CO)", "PT08.S2(NMHC)", "PT08.S3(NOx)", "PT08.S4(NO2)", "PT08.S5(O3)", "T", "RH", "AH", "CO(GT)"]
    return t[keep], "CO(GT)"


def gasturbine():
    t = pd.concat([pd.read_csv(raw(f"x_gt/gt_{y}.csv")) for y in range(2011, 2016)], ignore_index=True)
    return t.drop(columns=["CO"]), "NOX"


def paqmon():
    t = pd.read_csv(raw("paqmon.csv"))
    return t[["T_M1", "rH_M1", "PM10_M1", "PM25_M1", "PM25_SEPA"]], "PM25_SEPA"


def rouen():
    t = pd.read_csv(raw("rouen_ASE6.csv"), sep=";", na_values="NA")
    assert set(t.Location.dropna()) == {"SUD3"}
    keep = ["ASE_NO2", "ASE_NO", "ASE_CO", "ASE_Ox", "ASE_T", "ASE_HR", "ASE_PA", "SUD3_NO2"]
    return t[keep], "SUD3_NO2"


def kelmarsh():
    name = "Turbine_Data_Kelmarsh_1_2016-01-03_-_2017-01-01_228.csv"
    with zipfile.ZipFile(raw("kelmarsh_2016.zip")) as z:
        t = pd.read_csv(z.open(name), comment=None, skiprows=9)
    t.columns = [c.lstrip("# ").strip() for c in t.columns]
    cap = "Available Capacity for Production (kW)"
    full = (t["Data Availability"] == 1) & (t[cap] == t[cap].max())
    # The turbine's own "Wind speed, Standard deviation" is empty all 2016: the turbulence is sensor 1's; rows
    # without the nacelle temperature (26 %) are dropped here, or the general rule would drop the column.
    keep = ["Wind speed (m/s)", "Wind speed Sensor 1, Standard deviation (m/s)", "Nacelle ambient temperature (°C)",
            "Power (kW)"]
    t = t.loc[full, keep]
    return t.dropna(subset=["Nacelle ambient temperature (°C)"]), "Power (kW)"


def uhpc():
    return pd.read_excel(raw("uhpc.xls")), "CS"


def olympus(name):
    cfg = json.load(open(raw(f"olympus_{name}_config.json")))
    cols = [p["name"] for p in cfg["parameters"]] + [m["name"] for m in cfg["measurements"]]
    t = pd.read_csv(raw(f"olympus_{name}_data.csv"), names=cols)
    return t, cfg["measurements"][0]["name"]


def from_general(key, drop=()):
    t = pd.read_csv(os.path.join(TABLES, key.replace(":", "__") + ".csv"))
    return t.drop(columns=list(drop)), "target"


STATIC = {
    "niche:ccpp": ("ccpp", ccpp),
    "niche:yacht": ("yacht", yacht),
    "niche:synchronous_machine": ("synchronous_machine", syncmachine),
    "niche:qsar_aquatic": ("qsar", qsar_aquatic),
    "niche:qsar_bioconcentration": ("qsar", qsar_bcf),
    "niche:auto_mpg": ("auto_mpg", autompg),
    "niche:nikuradse": ("nikuradse", nikuradse),
    "niche:visualizing_galaxy": ("visualizing_galaxy", galaxy),
    "niche:esol": ("esol", esol),
    "niche:chf_zhao": ("chf", chf_zhao),
    "niche:chf_kaeri": ("chf", chf_kaeri),
    "niche:uhpc": ("uhpc", uhpc),
    "niche:cfd_wavy_channel": ("cfd_wavy_channel", cfd_wavy),
    "niche:olympus_suzuki": ("olympus", lambda: olympus("suzuki")),
    "niche:olympus_hplc": ("olympus", lambda: olympus("hplc")),
    "niche:airfoil_self_noise": ("airfoil", lambda: from_general("ctr23:airfoil_self_noise")),
    "niche:energy_efficiency": ("energy_efficiency", lambda: from_general("ctr23:energy_efficiency", ["cooling_load"])),
    "niche:grid_stability": ("grid_stability", lambda: from_general("ctr23:grid_stability", ["stabf_stable"])),
    "niche:qsar_fish_toxicity": ("qsar", lambda: from_general("ctr23:QSAR_fish_toxicity")),
    "niche:sulfur": ("sulfur", lambda: from_general("grinsztajn:sulfur", ["y2"])),
    "niche:elevators": ("elevators", lambda: from_general("grinsztajn:elevators")),
}
# Time series (user decision 02.11.2026: the split by time). One table a source: Rouen — the sensor with the most
# complete rows (ASE6, always at the SUD3 station); PAQMON — the first unit (M1); Kelmarsh — turbine 1, 2016, the
# rows where it was fully available (capacity at its maximum, complete 10 minutes) — chosen by the turbine's
# state, not by its power. MELFA (robot inverse dynamics) is left out: its data are only Python pickles, and
# unpickling a downloaded file runs code.
TIME = {
    "niche:air_quality_co": ("air_quality", airquality),
    "niche:gas_turbine_nox": ("gas_turbine", gasturbine),
    "niche:paqmon_pm25": ("paqmon", paqmon),
    "niche:rouen_no2": ("rouen", rouen),
    "niche:kelmarsh_power": ("kelmarsh", kelmarsh),
}


def time_split(n):
    k = int(round(0.75 * n))
    return {"time": dict(train=np.arange(k), test=np.arange(k, n), info=dict(first_test_row=k))}


def main():
    os.makedirs(TABLES, exist_ok=True)
    os.makedirs(SPLITS, exist_ok=True)
    tables, fam, kind, logs, shapes = {}, {}, {}, {}, {}
    for group, k in ((STATIC, "static"), (TIME, "time")):
        for key, (family, load) in group.items():
            df, target = load()
            for c in df.columns:                  # text that is all numbers becomes numbers, other text a category
                if not pd.api.types.is_numeric_dtype(df[c]):
                    num = pd.to_numeric(df[c], errors="coerce")
                    df[c] = num if num.notna().sum() == df[c].notna().sum() else df[c].astype(object)
            shapes[key] = df.shape
            tables[key], logs[key] = clean(df, target, key)
            fam[key], kind[key] = family, k
            print(f"{key:32s} {df.shape} -> {tables[key].shape}  {'; '.join(logs[key])}")
    families = sorted(set(fam.values()))
    perm = np.random.default_rng(SEED).permutation(len(families))
    working = {families[i] for i in perm[: len(families) // 2]}
    rows = []
    for key, t in tables.items():
        fn = key.replace(":", "__")
        tpath = os.path.join(TABLES, fn + ".csv")
        t.to_csv(tpath, index=False)
        sp = make_splits(t) if kind[key] == "static" else time_split(len(t))
        spath = os.path.join(SPLITS, fn + ".npz")
        np.savez_compressed(spath, **{f"{s}_{part}": v[part] for s, v in sp.items() for part in ("train", "test")})
        info = {s: v["info"] for s, v in sp.items()}
        with open(os.path.join(SPLITS, fn + ".json"), "w") as f:
            json.dump(info, f, indent=1)
        side = "work" if fam[key] in working else "test"
        rows.append([key, fam[key], side, kind[key], shapes[key][0], len(t), t.shape[1] - 1, ",".join(sorted(sp)),
                     info.get("xfeat", {}).get("on", ""), "; ".join(logs[key]), sha256(tpath), sha256(spath)])
    rows.sort(key=lambda r: (r[2] != "work", r[0].lower()))
    with open(os.path.join(REPO_DATA, "niche_assignment.tsv"), "w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["table", "family", "side", "kind", "rows_raw", "rows", "features", "splits", "xfeat_on", "cleaning",
                    "table_sha256", "splits_sha256"])
        w.writerows(rows)
    for s in ("work", "test"):
        print(s, sum(r[2] == s for r in rows), "tables,", len({r[1] for r in rows if r[2] == s}), "families")


if __name__ == "__main__":
    main()
