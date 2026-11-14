"""The fresh test suite (fnet/README.md §9.2–§9.3): 11 open engineering and physical tables, all of them test.

Rules fixed before any model is run on these tables (user decisions 03.11.2026):
- cleaning and splits as in prepare.py / niche_prepare.py (missing, categorical <= 10 levels, constants, <= 20 000
  rows, names; iid1, xfeat, xy) and the lower tails xfeat_lo, xy_lo (prepare.lower_splits; user decision 03.11.2026);
- not inputs: other outputs of the same system, columns derived from the target or computed from other inputs,
  identifiers, sources, authors, measurement metadata (per table below);
- repeated measurements of one object: iid1 by groups (75 % of the groups train) — electrolytes (one mixture at several
  temperatures), CHN-T1 (repeated wind-tunnel runs of the same condition);
- the particle-drag set (Zenodo 14283844) is left out: its data are per-run logs a table would be averaged from by
  choices of our own.
"""
import csv
import glob
import json
import os
import zipfile

import numpy as np
import pandas as pd

from common import DATA, REPO_DATA, sha256
from niche_prepare import TABLES, SPLITS
from prepare import clean, lower_splits, make_splits

RAW = os.path.join(DATA, "fresh", "raw")


def raw(*p):
    return os.path.join(RAW, *p)


def gravel():
    # H and R: the flow depth and hydraulic radius follow from Q = V·W·H — outputs, not inputs.
    with zipfile.ZipFile(raw("gravel", "Flow resistance data set and Rcode_march2025.zip")) as z:
        t = pd.read_csv(z.open("Flow resistance data set and Rcode/dataset.csv"), sep=";", encoding="latin-1")
    return t[["W(m)", "S", "Q(m3/s)", "D84", "V(m/s)"]], "V(m/s)", None


def pier_scour():
    t = pd.read_excel(raw("usgs", "psdb2014.xlsx"), sheet_name="Laboratory Data", header=2)
    t.columns = [" ".join(str(c).split()) for c in t.columns]
    keep = [c for c in t.columns if not c.startswith(("Data source", "Sheppard", "Unnamed"))]
    target = [c for c in keep if c.startswith("Pier-scour depth")][0]
    # sigma_g and the duration are numbers with a few text cells: as numbers (text -> missing).
    t = t[keep].copy()
    for c in keep:
        t[c] = pd.to_numeric(t[c], errors="coerce")
    return t, target, None


def co2_boiling():
    # Fluid properties and dimensionless numbers are functions of Ts (and of the inputs): only the primary ones.
    with zipfile.ZipFile(raw("co2", "JTEN_Zenodo_reproducibility_package_v1.zip")) as z:
        t = pd.read_csv(z.open("data/dataset_692_revised.csv"))
    return t[["D", "x", "G", "q", "Ts", "h"]], "h", None


def orifice():
    # Area ratio (from Beta), rho_ratio, x, d, Ao, m.tp, Cc: computed from the others; Dp.L, Dp.G, X, X^2, the
    # two-phase multiplier: from the target or single-phase models; Data: the source.
    t = pd.read_csv(raw("orifice", "pressure_drop_dataset.csv"), encoding="utf-8-sig")
    return t[["V_SL", "V_SG", "t/d", "D", "Beta", "rho_G", "rho_L", "DP_TP"]], "DP_TP", None


def packings():
    # V_G and F follow from u_G (the column's area, the gas density); h_L is the other output.
    t = pd.read_csv(raw("packing", "dataset_ceramic_packings.csv"), sep=";", encoding="utf-8-sig", skiprows=[1])
    t.columns = ["Packing"] + list(t.columns[1:])
    keep = ["Packing", "u_G", "u_L", "T_G,in", "T_L,in", "ϕ", "Δp/H"]
    return t[keep], "Δp/H", None


def chnt1():
    files = sorted(glob.glob(raw("chnt1", "*.csv")))
    t = pd.concat([pd.read_csv(f) for f in files], ignore_index=True).drop_duplicates()
    t = t[["Ma", "Alpha", "Beta", "Re", "CL"]]
    groups = t[["Ma", "Alpha", "Beta", "Re"]].round(2).astype(str).agg("|".join, axis=1)
    return t, "CL", groups


def alkanes():
    t = pd.read_csv(raw("alkane", "AlkaneC4toC16.csv"), encoding="utf-8-sig")
    t["carbon_number"] = t["Fuel"].str.count("C")            # SMILES of n-alkanes: one C a carbon
    keep = ["T(K)", "P(atm)", "Equv(phi)", "Fuel(%)", "Oxidizer(%)", "Diluant(%)", "Diluant Type", "carbon_number",
            "Time(μs)"]
    return t[keep], "Time(μs)", None


def sfrc():
    # Vu (kN): the shear at failure without self-weight; Pu, vu and the normalised forms, Veg, Vutot, moments: from it.
    t = pd.read_excel(raw("sfrc", "database SFRC.xlsx"), header=None)
    names = [str(x).strip() for x in t.iloc[1]]
    data = t.iloc[3:].reset_index(drop=True)
    data.columns = [f"{n}#{i}" for i, n in enumerate(names)]
    pick = {"b#2": "b", "d#4": "d", "a/d#18": "a_over_d", "ρ#16": "rho", "fy#17": "fy", "fc#21": "fc",
            "daggmax#20": "daggmax", "Vf#25": "Vf", "L/d#27": "fiber_aspect", "ftenfiber#28": "f_fiber",
            "Vu#35": "Vu"}
    out = data[list(pick)].rename(columns=pick)
    return out, "Vu", None


def corroded():
    t = pd.read_csv(raw("corroded", "Database.csv"), encoding="utf-8-sig")
    t.columns = [c.strip() for c in t.columns]
    keep = ["Width (mm)", "Depth (mm)", "Test Length (mm)", "Bottom Cover to Ctr of Tension Bar (mm)", "# Tensile Bars",
            "Diameter Tensile Bars, db,t (mm)", "Tension Reinforcement Ratio, pten (%)",
            "Comp Reinforcement Ratio, pcom (%)", "fy Longitudinal Bars (Tensile), (MPa)", "f'c (MPa)",
            "Mass Loss (Tensile bars), ηm (%)", "Shear Span, x (mm)", "Stirrup Volumetric Ratio, ρs", "W/C Ratio",
            "Mmax,exp (kNm)"]
    return t[keep], "Mmax,exp (kNm)", None


def soil():
    # Gravimetric water content follows from the volumetric one and the density; Cation and Anion from the salt
    # type; the original content and molar mass describe the salt, the concentration follows from them.
    t = pd.read_excel(raw("soil", "A database of soil thermal conductivity incorporating salts effects.xlsx"),
                      sheet_name="data", skiprows=[1])
    keep = ["Temperature", "Sand_Content", "Silt_Content", "Clay_Content", "Bulk_Density", "volumetric_Water_Content",
            "Salt_Type", "Soil_Salt_Content", "Soil_Thermal_Conductivity"]
    keep = [k if k in t.columns else [c for c in t.columns if c.startswith(k[:18])][0] for k in keep]
    return t[keep], keep[-1], None


def electrolytes():
    t = pd.read_csv(raw("electrolyte", "Conductivtiy_experiment.csv"), sep=";", skiprows=[1, 2],
                    usecols=["temperature", "PC", "EC", "EMC", "LiPF_6", "EIS_conductivity"])
    t = t[pd.to_numeric(t["EIS_conductivity"], errors="coerce") > 0]
    groups = t[["PC", "EC", "EMC", "LiPF_6"]].astype(float).round(4).astype(str).agg("|".join, axis=1)
    return t, "EIS_conductivity", groups


SOURCES = {
    "fresh:gravel_flow_resistance": gravel,
    "fresh:pier_scour_lab": pier_scour,
    "fresh:co2_flow_boiling": co2_boiling,
    "fresh:orifice_two_phase_dp": orifice,
    "fresh:ceramic_packings_dp": packings,
    "fresh:chnt1_lift": chnt1,
    "fresh:alkane_ignition_delay": alkanes,
    "fresh:sfrc_shear": sfrc,
    "fresh:corroded_rc_beams": corroded,
    "fresh:soil_thermal_conductivity": soil,
    "fresh:electrolyte_conductivity": electrolytes,
}


def group_split(groups, seed=1):
    g = pd.Series(groups).reset_index(drop=True)
    names = np.array(sorted(g.unique()))
    perm = np.random.default_rng(seed).permutation(len(names))
    train_names = set(names[perm[: int(round(0.75 * len(names)))]])
    is_train = g.isin(train_names).to_numpy()
    return dict(train=np.flatnonzero(is_train), test=np.flatnonzero(~is_train),
                info=dict(seed=seed, by="groups", groups=int(len(names))))


def main():
    rows = []
    for key, load in SOURCES.items():
        df, target, groups = load()
        df = df.reset_index(drop=True)
        for c in df.columns:
            if not pd.api.types.is_numeric_dtype(df[c]):
                num = pd.to_numeric(df[c], errors="coerce")
                df[c] = num if num.notna().sum() == df[c].notna().sum() else df[c].astype(object)
        shape = df.shape
        if groups is not None:
            df = df.assign(__group=pd.Series(groups).reset_index(drop=True).to_numpy())
        # clean() drops rows and may subsample: the groups ride along as a categorical-free column and are removed
        g = df.pop("__group") if "__group" in df else None
        if g is not None:
            df["gidcol"] = pd.factorize(g)[0].astype(float)
        t, log = clean(df, target, key)
        gid = t.pop("gidcol") if "gidcol" in t else None
        fn = key.replace(":", "__")
        tpath = os.path.join(TABLES, fn + ".csv")
        t.to_csv(tpath, index=False)
        sp = make_splits(t)
        sp.update(lower_splits(t, sp.get("xfeat", {}).get("info", {}).get("on", "")))
        if gid is not None:
            sp["iid1"] = group_split(gid.to_numpy())
        for s in ("iid2", "iid3"):
            sp.pop(s, None)
        spath = os.path.join(SPLITS, fn + ".npz")
        np.savez_compressed(spath, **{f"{s}_{part}": v[part] for s, v in sp.items() for part in ("train", "test")})
        info = {s: v["info"] for s, v in sp.items()}
        with open(os.path.join(SPLITS, fn + ".json"), "w") as f:
            json.dump(info, f, indent=1)
        rows.append([key, key.split(":")[1], "test", "static", shape[0], len(t), t.shape[1] - 1, ",".join(sorted(sp)),
                     info.get("xfeat", {}).get("on", ""), "; ".join(log), sha256(tpath), sha256(spath)])
        print(f"{key:36s} {shape} -> {t.shape}  splits {','.join(sorted(sp))}  {'; '.join(log)}")
    with open(os.path.join(REPO_DATA, "fresh_assignment.tsv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["table", "family", "side", "kind", "rows_raw", "rows", "features", "splits", "xfeat_on", "cleaning",
                    "table_sha256", "splits_sha256"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
