"""The third test suite (fnet/README.md 11): open engineering and physical tables, all of them test.

Rules fixed before any model is run on these tables (user decision 05.11.2026; the same as for the fresh suite):
- cleaning and splits as in prepare.py (missing, categorical <= 10 levels, constants, <= 20 000 rows, names; iid1, xfeat,
  xy) and the lower tails xfeat_lo, xy_lo (prepare.lower_splits);
- not inputs: other outputs of the same system, columns derived from the target or computed from other inputs,
  identifiers, sources, authors, measurement metadata (per table below);
- iid1 by groups (75 % of the groups train): repeated measurements of one object by that object (a soil site, an ionic
  liquid, a nanofluid mixture, an airfoil, a clay sample, a biomass); in the other tables replicates — rows with the same
  inputs — form a group (no leak through identical inputs);
- a table that fails a check drops out without replacement: wave runup (Auckland figshare 7732967) — the download is
  refused (403 from the institution's object store, 05.11.2026); the bentonite sheet of the swelling set — 296 rows
  (< 300) and other inputs and units than the natural clays;
- footnote letters in cells are dropped, the numbers kept as published (biomass: b — the maximum of a range,
  c — the yield by difference); the authors' own exclusions for their models are not applied.
"""
import csv
import gzip
import io
import json
import os
import re
import zipfile

import numpy as np
import pandas as pd

from common import DATA, REPO_DATA, sha256
from fresh_prepare import group_split
from niche_prepare import TABLES, SPLITS
from prepare import clean, lower_splits, make_splits

RAW = os.path.join(DATA, "third", "raw")


def raw(*p):
    return os.path.join(RAW, *p)


def by_inputs(t, target):
    """Groups of replicates: rows with the same inputs."""
    x = t.drop(columns=[target])
    return x.apply(lambda r: "|".join(str(v) for v in r), axis=1)


def soil_ksat():
    # Laboratory Ksat only (field methods differ); log10 of it, its customary scale (four orders of magnitude). Not
    # inputs: water retention at 33 and 1500 kPa (other outputs), the texture class (from sand, silt, clay), pH (a
    # chemistry measurement of other sites), coordinates, horizon names, sources.
    with gzip.open(raw("soilksat", "sol_ksat.pnts_horizons.csv.gz")) as f:
        t = pd.read_csv(f, low_memory=False)
    t = t[pd.to_numeric(t["ksat_lab"], errors="coerce") > 0].copy()
    t["log10_ksat_lab"] = np.log10(t["ksat_lab"].astype(float))
    cols = ["clay_tot_psa", "silt_tot_psa", "sand_tot_psa", "db", "oc_v", "hzn_depth", "log10_ksat_lab"]
    return t[cols], "log10_ksat_lab", t["site_key"]


def cfst():
    # Circular CFST columns under axial compression (the set's largest sheet). Not inputs: source, reference, year,
    # specimen, notes.
    t = pd.read_excel(raw("cfst", "3208 database for uploading.xlsx"), sheet_name="C_CFST_NM", header=4)
    t.columns = [str(c).strip() for c in t.columns]
    cols = ["D (mm)", "t (mm)", "L (mm)", "fy (MPa)", "fu (MPa)", "Ea (Gpa)", "fc (MPa)", "Ec (Gpa)", "fc type", "N Test (kN)"]
    t = t[cols]
    return t, "N Test (kN)", by_inputs(t, "N Test (kN)")


def co2_ionic_liquids():
    # Not inputs: the measurement type (solubility or capacity), the colour index, DOI, origin, SMILES.
    with zipfile.ZipFile(raw("co2il", "CO2_in_ILs_database_1_1_0.zip")) as z:
        b = z.read("CO2_in_ILs_database_1_1_0/descriptors_COS_in_ILs_db_1_1_0.ods")
    t = pd.read_excel(io.BytesIO(b), engine="odf", sheet_name="data_final_descripteur")
    cols = ["T / K", "P / bar", "eta_C / kcal.mol-1", "eta_A / kcal.mol-1", "chi_C / kcal.mol-1", "chi_A / kcal.mol-1",
            "mu_C / D", "mu_A / D", "NPR1 C", "NPR2 C", "NPR1 A", "NPR2 A", "Stoichiometry", "x_CO2"]
    cols[12:12] = [c for c in t.columns if str(c).startswith(("Rg C", "Rg A"))]   # "/ Å" with either angstrom sign
    return t[cols], "x_CO2", t["IL"]


def mwcnt():
    # The measured thermal conductivity of the nanofluids; the sheet stores 1 + phi and 1 + alpha (MWCNT and ethylene
    # glycol fractions), given back as phi and alpha. Not inputs: the base-fluid conductivity (a correlation of T and
    # alpha), k/k_base (from the target), T/Tmax (from T); viscosity is another output (other sheets).
    t = pd.read_excel(raw("mwcnt", "Final Thermal Conductivity and Viscosity_Graphs_160522_Adjustments.xlsx"),
                      sheet_name="k Consolidated")
    t = pd.DataFrame({"T": t["T"], "phi": t["1+phi"] - 1, "alpha": t["1+alpha"] - 1, "k": t["K"]})
    groups = t[["phi", "alpha"]].astype(float).round(6).astype(str).agg("|".join, axis=1)
    return t, "k", groups


def swelling():
    # Natural clays (the sheet N1-N5). Not inputs: the activity A = IP / C and IP = wL - wP (derived), sample, study
    # area, soil type, source.
    t = pd.read_excel(raw("swelling", "data_swelling_pressure.xlsx"), sheet_name="Natural Clay(N1-N5)")
    t.columns = [" ".join(str(c).split()) for c in t.columns]
    target = [c for c in t.columns if c.endswith("[MPa]")][0]
    inputs = [c for c in t.columns if c.startswith(("Gravel", "Sand", "Silt", "C (", "wL", "wP", "γd", "wi"))] + ["Test"]
    groups = t["Source"].astype(str).str.strip() + "|" + t["Sample"].astype(str).str.strip()
    out = t[inputs + [target]].rename(columns={target: "Ps [MPa]"})
    return out, "Ps [MPa]", groups


def frp_uhpc():
    # Not inputs: the reference and the failure mode (another output).
    t = pd.read_excel(raw("frp_uhpc", "Dataset of bond strength and failure mode between FRP bars and UHPC or UHPSSC.xlsx"),
                      sheet_name="Dataset", header=1)
    t.columns = [" ".join(str(c).split()) for c in t.columns]
    target = [c for c in t.columns if c.startswith("Bond strength")][0]
    drop = [c for c in t.columns if c.startswith(("Reference", "Failure mode"))]
    t = t.drop(columns=drop)
    return t, target, by_inputs(t, target)


def airfoil_cl():
    # CFD (OpenFOAM) at Re = 1e5: the lift coefficient from the angle of attack and the 8 CST shape
    # coefficients. Not inputs: Cd (another output), the file name.
    t = pd.read_csv(raw("airfoil", "COMPILED AIRFOIL DATA.csv"))
    t.columns = [c.strip() for c in t.columns]
    cols = ["AoA"] + [f"CST Coeff {k}" for k in range(1, 9)] + ["Cl"]
    return t[cols], "Cl", t["Filename"].astype(str).str.strip()


def kiln():
    # Simulated rotary kilns: each case (listOfCases.csv: D, d/D, Fr, Re_omega, beta, L/D) at several Peclet numbers
    # (one log per Pe); the target is the mean residence time Tau at the outlet — the log's last line. Not inputs: the
    # profiles along the kiln (other outputs).
    rows = []
    with zipfile.ZipFile(raw("kiln", "supplementary.zip")) as z:
        cases = pd.read_csv(io.StringIO(z.read("supplementary/listOfCases.csv").decode("latin-1")))
        cases.columns = [c.strip() for c in cases.columns]
        for info in z.infolist():
            m = re.fullmatch(r"supplementary/(\d+)/logFiles/log_Pe([0-9.]+)", info.filename)
            if not m:
                continue
            lines = z.read(info).decode("latin-1").strip().splitlines()
            head = lines[0].split("\t")
            last = lines[-1].split("\t")
            if len(last) != len(head):
                continue
            rows.append((int(m.group(1)), float(m.group(2)), float(last[head.index("Tau,s")])))
    r = pd.DataFrame(rows, columns=["case ID", "Pe", "Tau_s"]).sort_values(["case ID", "Pe"])
    t = cases.merge(r, on="case ID").drop(columns=["case ID"])
    return t, "Tau_s", by_inputs(t, "Tau_s")


def biomass():
    # Not inputs: the biomass name, its origin, the reference. Footnote letters dropped (see the module notes).
    t = pd.read_excel(raw("biomass", "Biomass pyrolysis dataset.xlsx"), sheet_name="Database")
    t = t[t.iloc[:, 1].notna() & t.iloc[:, 11].notna()].copy()
    t.columns = [" ".join(str(c).split()) for c in t.columns]
    num = lambda s: pd.to_numeric(s.astype(str).str.replace(r"[a-zA-Z]+$", "", regex=True).str.strip(), errors="coerce")
    out = pd.DataFrame({
        "Cellulose [%]": num(t["Cellulose [%]"]), "Hemicellulose [%]": num(t["Hemicellulose [%]"]),
        "Lignin [%]": num(t["Lignin [%]"]),
        "Reactor": t["Type of reactor"].astype(str).str.strip().str.replace(r"(?<=bed)a$", "", regex=True),
        "Temperature [C]": num(t[[c for c in t.columns if c.startswith("Pyrolysis temperature")][0]]),
        "Heating rate [C/min]": num(t[[c for c in t.columns if c.startswith("Heating rate")][0]]),
        "N2 flow [mL/min]": num(t[[c for c in t.columns if c.startswith("N2 flow")][0]]),
        "Particle size": num(t[[c for c in t.columns if c.startswith("Biomass particle size")][0]]),
        "Bio-oil yield [%]": num(t["Bio-oil yield [%]"]),
    })
    groups = t["Biomass"].astype(str).str.strip().str.replace(r"1$", "", regex=True)
    return out, "Bio-oil yield [%]", groups


SOURCES = {
    "third:soil_ksat": soil_ksat,
    "third:cfst_columns": cfst,
    "third:co2_ionic_liquids": co2_ionic_liquids,
    "third:mwcnt_nanofluid_k": mwcnt,
    "third:clay_swelling": swelling,
    "third:frp_uhpc_bond": frp_uhpc,
    "third:airfoil_cl": airfoil_cl,
    "third:kiln_residence": kiln,
    "third:biomass_pyrolysis": biomass,
}


def main():
    rows = []
    for key, load in SOURCES.items():
        df, target, groups = load()
        df = df.reset_index(drop=True)
        groups = pd.Series(groups).reset_index(drop=True)
        for c in df.columns:
            if not pd.api.types.is_numeric_dtype(df[c]):
                num = pd.to_numeric(df[c], errors="coerce")
                df[c] = num if num.notna().sum() == df[c].notna().sum() else df[c].astype(object)
        shape = df.shape
        # clean() drops rows and may subsample: the groups ride along as a numeric column and are removed after.
        df["gidcol"] = pd.factorize(groups)[0].astype(float)
        t, log = clean(df, target, key)
        gid = t.pop("gidcol")
        fn = key.replace(":", "__")
        tpath = os.path.join(TABLES, fn + ".csv")
        t.to_csv(tpath, index=False)
        sp = make_splits(t)
        sp.update(lower_splits(t, sp.get("xfeat", {}).get("info", {}).get("on", "")))
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
        print(f"{key:30s} {shape} -> {t.shape}  groups {info['iid1']['groups']}  splits {','.join(sorted(sp))}  {'; '.join(log)}",
              flush=True)
    with open(os.path.join(REPO_DATA, "third_assignment.tsv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["table", "family", "side", "kind", "rows_raw", "rows", "features", "splits", "xfeat_on", "cleaning",
                    "table_sha256", "splits_sha256"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
