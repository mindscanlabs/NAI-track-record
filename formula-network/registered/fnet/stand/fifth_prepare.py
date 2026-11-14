"""The fifth test suite (fnet/README.md 25): open engineering and physical tables chosen by the product's scope
(fnet/PRODUCT.md 5; criteria K1-K5 of README 14.1), all of them test. Sources: fifth_fetch.sh (checksums:
fifth_checksums.py).

Rules fixed before any model is run on these tables (the same as for the fourth suite):
- cleaning and splits as in prepare.py (missing, categorical <= 10 levels, constants, <= 20 000 rows, names; iid1, xfeat,
  xy) and the lower tails xfeat_lo, xy_lo (prepare.lower_splits);
- not inputs: other outputs of the same system, columns derived from the target or computed from other inputs,
  identifiers, sources, authors, apparatus, measurement metadata and uncertainties, other models' predictions and
  fits (per table below);
- iid1 by groups (75 % of the groups train): repeated measurements or variants of one object by that object (a beam
  section, an angle sweep of the wire, a measurement run, a paper and material); in the other tables rows with the
  same inputs form a group;
- a code standing for a category (the layup class, the solvus type) is a category, not a number.
"""
import csv
import json
import os

import numpy as np
import pandas as pd

from common import DATA, REPO_DATA, sha256
from fresh_prepare import group_split
from niche_prepare import TABLES, SPLITS
from prepare import clean, lower_splits, make_splits
from third_prepare import by_inputs

RAW = os.path.join(DATA, "fifth", "raw")


def raw(*p):
    return os.path.join(RAW, *p)


def ahmed_cd():
    # AhmedML (Hugging Face neashton/ahmedml, CC BY-SA 4.0): the drag coefficient of an Ahmed body, hybrid RANS-LES
    # CFD, 500 geometries. Not inputs: cl (another output), slant-angle-length and slant-angle-height (the slant
    # surface's projections: computed from its length and angle). Joined on run (one geometry row is missing).
    g = pd.read_csv(raw("ahmedml_geo_parameters_all.csv"))
    f = pd.read_csv(raw("ahmedml_force_mom_all.csv"))
    g.columns = [c.strip() for c in g.columns]
    f.columns = [c.strip() for c in f.columns]
    t = g.merge(f, on="run", how="inner")
    cols = ["body-length", "body-height", "body-width", "front-arc-diameter", "slant-surface-length",
            "slant-angle-degrees", "cd"]
    t = t[cols]
    return t, "cd", by_inputs(t, "cd")


def lsf_wall_u():
    # Light-gauge steel-framed wall (Mendeley 247pvf6whn v1, CC BY 4.0, COMSOL, 5 000 random designs): the U-value.
    # Not inputs: wall_total_thickness_mm (the sum of layer thicknesses), R_total (about 1 / U), the heat flux and the
    # two surface temperatures (other outputs).
    t = pd.read_excel(raw("lsf_wall.xlsx"), sheet_name=0)
    cols = ["keel_spacing_mm", "keel_width_mm", "keel_height_mm", "insulation_thickness_mm", "insulation_k_W_mK",
            "gypsum_k_W_mK", "steel_k_W_mK", "panel_width_m", "panel_height_m", "h_inside_W_m2K", "h_outside_W_m2K",
            "T_inside_C", "T_outside_C", "U_value_W_m2K"]
    t = t[cols]
    return t, "U_value_W_m2K", by_inputs(t, "U_value_W_m2K")


def curing_distortion():
    # Curing distortion of flat composite panels (Zenodo 19450971, CC BY 4.0, FE, 6 000 cases): the largest absolute
    # out-of-plane deformation. The layup class is a category. Rows whose results were not read (read_ok false) are
    # dropped. Not inputs: Thickness, Area, Ratio, Volume, z0 (computed from the inputs), z_def_field, z_def_min,
    # z_def_max (other outputs), the mesh and solver statistics, case_id, case_dir.
    t = pd.read_csv(raw("curing_didearot_flatpanel_db.csv"))
    ok = t["read_ok"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    t = t[ok].copy()
    t["class_id"] = "class " + t["class_id"].astype(str)
    cols = ["Lx", "Ly", "t_ply", "Nplies", "class_id", "z_def_max_abs"]
    t = t[cols]
    return t, "z_def_max_abs", by_inputs(t, "z_def_max_abs")


def cellular_beams():
    # Laterally restrained cellular steel beams (Mendeley zcm29bp7yf v2, CC BY 4.0, FE): the ultimate load wu. Not
    # inputs: wcr (another load output), H/ho, s/ho, L/H, so, se and the number of openings (computed from the
    # geometry), the row number. A section (H, bf, tw, tf) is one group.
    t = pd.read_csv(raw("cellular_beams_CBR.csv"))
    t.columns = [c.strip().strip('"') for c in t.columns]
    cols = ["H (mm)", "bf (mm)", "tw (mm)", "tf (mm)", "L (mm)", "ho (mm)", "s (mm)", "fy (MPa)", "wu (kN/m)"]
    t = t[cols].apply(pd.to_numeric, errors="coerce")
    groups = t[["H (mm)", "bf (mm)", "tw (mm)", "tf (mm)"]].astype(str).agg("|".join, axis=1)
    return t, "wu (kN/m)", groups


def hts_ic():
    # The critical current of a SuperOx GdBCO HTS wire (figshare 3759315, CC BY 4.0; the item of the collection the
    # search opened, not chosen by its values): Ic from the measured temperature, field and angle. Rows without a
    # measured Ic ('--') are dropped. Not inputs: Ic/w (Ic per width), n, V0, V1 (fits of the same IV curves), the Hall
    # field and angle (a second measurement of the field and angle), the set values (nominal). An angle sweep (set
    # temperature and set field) is one group.
    t = pd.read_excel(raw("hts_superox_all_data.xlsx"), sheet_name=0)
    t.columns = [str(c).strip() for c in t.columns]
    temp = [c for c in t.columns if c.startswith("Temperature")][0]
    field = [c for c in t.columns if c.startswith("Field")][0]
    angle = [c for c in t.columns if c.startswith("Angle")][0]
    set_t = [c for c in t.columns if c.startswith("Set temperature")][0]
    set_b = [c for c in t.columns if c.startswith("Set field")][0]
    out = pd.DataFrame({"T_K": pd.to_numeric(t[temp], errors="coerce"), "B_T": pd.to_numeric(t[field], errors="coerce"),
                        "angle_deg": pd.to_numeric(t[angle], errors="coerce"),
                        "Ic_A": pd.to_numeric(t["Ic (A)"], errors="coerce")})
    groups = t[set_t].astype(str) + "|" + t[set_b].astype(str)
    keep = out["Ic_A"].notna()
    return out[keep], "Ic_A", groups[keep]


def zr_hydrogen_tss():
    # Terminal solid solubility of hydrogen in zirconium alloys (Zenodo 23954638 v1, CC BY 4.0; a compilation of 59
    # publications): the hydrogen concentration at the solvus from the temperature, the solvus type (a category:
    # dissolution, precipitation and their variants) and the alloying contents. Not inputs: h (the sample's hydrogen
    # content, the same quantity as the target), the Arrhenius and diffusion fits and the min / max columns (fits and
    # summaries of the data), uncertainties, the alloy's name (its composition is given), methods, devices, sources and
    # every descriptive column; the cold work and irradiation columns go by the general rules (missing). A measurement
    # run is one group.
    t = pd.read_csv(raw("tss_TSS_DATASET_v1.csv"), sep=";", decimal=",", low_memory=False, encoding="latin-1")
    t.columns = [c.strip() for c in t.columns]
    num = ["temperature", "sn", "fe", "cr", "ni", "nb", "n", "o", "cold_work", "hydrogen_concentration"]
    out = pd.DataFrame({c: pd.to_numeric(t[c], errors="coerce") for c in num})
    out.insert(1, "solvus_type", t["solvus_type"].astype(str).str.strip().where(t["solvus_type"].notna()))
    out["irradiated"] = t["irradiated"].astype(str).str.strip().where(t["irradiated"].notna())
    groups = t["identification"].astype(str) + "|" + t["run_id"].astype(str)
    keep = out["hydrogen_concentration"].notna() & out["temperature"].notna()
    return out[keep], "hydrogen_concentration", groups[keep]


def lpbf_density():
    # Laser powder bed fusion, process parameters and the relative density (Zenodo 6514897 v1.1, CC BY 4.0; a
    # compilation of 164 papers): the density / consolidation (%). The header is the sheet's second row; '-' marks a
    # missing value. Inputs: the process parameters (power, speed, layer thickness, hatch spacing, beam size, focus
    # offset, scanning strategy, layer rotation, island size, build plate temperature), the material and whether the
    # part was treated (HIP); the material (17 levels) and sparse columns go by the general rules. Not inputs: the three
    # energy densities (computed from the parameters), the paper, the printer's maker and model (apparatus), the density
    # method and error, the heat-treatment details and every other property. A paper and material is one group.
    t = pd.read_excel(raw("lpbf_v1.1.xlsx"), sheet_name=0, header=1)
    t.columns = [" ".join(str(c).split()) for c in t.columns]
    t = t.replace("-", np.nan)
    pick = {"Material": "Material", "Laser power (W)": "power_W", "Laser speed (mm/s)": "speed_mm_s",
            "Layer thickness (um)": "layer_um", "Hatch spacing (um)": "hatch_um", "Beam size (um)": "beam_um",
            "Focus Offset (mm)": "focus_offset_mm", "Scanning strategy": "scan_strategy",
            "layer rotation (degree)": "layer_rotation_deg", "Island/Stripe size (mm)": "island_mm",
            "Build plate temperature (°C)": "plate_C", "Treated (HIP/Y/N)": "treated",
            "Density/Consolidation (%)": "density_pct"}
    cols = {}
    for src, dst in pick.items():
        hit = [c for c in t.columns if c.replace("�", "°") == src]
        if len(hit) != 1:
            raise SystemExit(f"lpbf: column {src!r}: {hit}")
        cols[dst] = t[hit[0]]
    out = pd.DataFrame(cols)
    for c in ("power_W", "speed_mm_s", "layer_um", "hatch_um", "beam_um", "focus_offset_mm", "layer_rotation_deg",
              "island_mm", "plate_C", "density_pct"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ("Material", "scan_strategy", "treated"):
        out[c] = out[c].astype(str).str.strip().where(out[c].notna())
    author = [c for c in t.columns if c.startswith("Author")][0]
    groups = t[author].astype(str) + "|" + t["Year"].astype(str) + "|" + out["Material"].astype(str)
    keep = out["density_pct"].notna()
    return out[keep], "density_pct", groups[keep]


SOURCES = {
    "fifth:ahmed_body_cd": ahmed_cd,
    "fifth:lsf_wall_u": lsf_wall_u,
    "fifth:composite_curing_distortion": curing_distortion,
    "fifth:cellular_beam_wu": cellular_beams,
    "fifth:hts_wire_ic": hts_ic,
    "fifth:zr_hydrogen_tss": zr_hydrogen_tss,
    "fifth:lpbf_density": lpbf_density,
}
CATEGORIES = {"class_id", "solvus_type", "irradiated", "Material", "scan_strategy", "treated"}


def main():
    rows = []
    for key, load in SOURCES.items():
        df, target, groups = load()
        df = df.reset_index(drop=True)
        groups = pd.Series(groups).reset_index(drop=True)
        for c in df.columns:
            if c in CATEGORIES:
                df[c] = df[c].astype(object)
            elif not pd.api.types.is_numeric_dtype(df[c]):
                num = pd.to_numeric(df[c], errors="coerce")
                df[c] = num if num.notna().sum() == df[c].notna().sum() else df[c].astype(object)
        shape = df.shape
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
        print(f"{key:36s} {shape} -> {t.shape}  groups {info['iid1']['groups']}  splits {','.join(sorted(sp))}  "
              f"xfeat on {info.get('xfeat', {}).get('on', '-')}  {'; '.join(log)}", flush=True)
    with open(os.path.join(REPO_DATA, "fifth_assignment.tsv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["table", "family", "side", "kind", "rows_raw", "rows", "features", "splits", "xfeat_on", "cleaning",
                    "table_sha256", "splits_sha256"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
