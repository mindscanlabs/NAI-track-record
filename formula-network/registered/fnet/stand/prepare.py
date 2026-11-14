"""Step 2 (P0): clean tables, source families, the CTR23 lottery, working/test assignment, splits.

All rules are fixed here before any model is run (fnet/README.md §6):
- target: CTR23 task target, PMLB "target", Grinsztajn last column;
- columns with > 20 % missing are dropped, then rows with any missing value;
- categorical (ARFF nominal, text): <= 10 levels -> one-hot without the most frequent level; more -> dropped;
- constant columns dropped; more than 20 000 rows -> a fixed random subsample of 20 000;
- column names: [A-Za-z0-9_], no leading digit, NAI's reserved names renamed (docs/TABLE_FORMAT.md);
- families: one source data = one family (FAMILIES below + a target-distribution check across suites);
- lottery: CTR23 families, seed 20261101, half to the working part; a PMLB or Grinsztajn copy of a source
  gives way: Grinsztajn is test unless its family is working on the CTR23 side; PMLB is working unless its
  family has a member elsewhere;
- splits per table: iid1..iid3 (75/25, seeds 1..3); xfeat — the feature (>= 20 distinct values) with the largest
  |Spearman rho| with the target, train at or below its 80 % quantile, test above (test share 10–30 %, else the
  next feature); xy — the same by the target itself, if it has >= 20 distinct values (amended 01.11.2026 after
  the fast baselines: solar_flare's lower 80 % were all zero).
"""
import csv
import gzip
import io
import json
import os
import re
import zlib

import numpy as np
import pandas as pd
from scipy import stats

from common import META, RAW, REPO_DATA, SPLITS, TABLES, sha256

SEED = 20261101
MAX_ROWS = 20000
MAX_LEVELS = 10
MAX_MISSING = 0.20
RESERVED = {"sigma", "sd", "se", "err", "error", "trials"}

FAMILIES = {
    "abalone": ["ctr23:abalone", "grinsztajn:abalone"],
    "brazilian_houses": ["ctr23:brazilian_houses", "grinsztajn:Brazilian_houses"],
    "california_housing": ["ctr23:california_housing", "grinsztajn:houses", "pmlb:537_houses"],
    "cpu": ["ctr23:cpu_activity", "grinsztajn:cpu_act", "pmlb:197_cpu_act", "pmlb:573_cpu_act",
            "pmlb:227_cpu_small", "pmlb:562_cpu_small"],
    "diamonds": ["ctr23:diamonds", "grinsztajn:diamonds"],
    "kings_county": ["ctr23:kings_county", "grinsztajn:house_sales"],
    "miami_housing": ["ctr23:miami_housing", "grinsztajn:MiamiHousing2016"],
    "superconductivity": ["ctr23:superconductivity", "grinsztajn:superconduct"],
    "wine": ["ctr23:red_wine", "ctr23:white_wine", "grinsztajn:wine_quality"],
    "solar_flare": ["ctr23:solar_flare", "pmlb:solar_flare"],
    "puma": ["ctr23:pumadyn32nh", "pmlb:225_puma8NH"],
    "census_house": ["grinsztajn:house_16H", "pmlb:574_house_16H", "pmlb:218_house_8L"],
    "pol": ["grinsztajn:pol", "pmlb:201_pol"],
}


# ---------------------------------------------------------------- reading

def split_arff_line(line):
    """Values of one dense ARFF data line: commas outside single or double quotes."""
    out, cur, q, i = [], [], None, 0
    while i < len(line):
        c = line[i]
        if q:
            if c == "\\" and i + 1 < len(line):
                cur.append(line[i + 1])
                i += 2
                continue
            if c == q:
                q = None
            else:
                cur.append(c)
        elif c in "'\"":
            q = c
        elif c == ",":
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur).strip())
    return out


def read_arff(path):
    names, nominal, rows, data = [], [], [], False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("%"):
                continue
            if not data:
                low = s.lower()
                if low.startswith("@attribute"):
                    m = re.match(r"@attribute\s+('([^']*)'|\"([^\"]*)\"|(\S+))\s+(.*)$", s, re.I)
                    name = m.group(2) or m.group(3) or m.group(4)
                    typ = m.group(5).strip()
                    names.append(name)
                    nominal.append(typ.startswith("{") or typ.lower().startswith(("string", "date")))
                elif low.startswith("@data"):
                    data = True
                continue
            if s.startswith("{"):
                raise RuntimeError(f"sparse ARFF not supported: {path}")
            rows.append(split_arff_line(s))
    df = pd.DataFrame(rows, columns=names).replace("?", np.nan)
    for n, nom in zip(names, nominal):
        df[n] = df[n].astype("object") if nom else pd.to_numeric(df[n], errors="coerce")
    return df


def load(suite, name, ctr23_targets):
    if suite == "ctr23":
        did = ctr23_targets[name]["did"]
        return read_arff(os.path.join(RAW, "ctr23", f"{did}_{name}.arff")), ctr23_targets[name]["target"]
    if suite == "pmlb":
        with gzip.open(os.path.join(RAW, "pmlb", f"{name}.tsv.gz"), "rt") as f:
            return pd.read_csv(f, sep="\t"), "target"
    df = pd.read_csv(os.path.join(RAW, "grinsztajn", f"{name}.csv"))
    return df, df.columns[-1]


# ---------------------------------------------------------------- cleaning

def clean_name(n, used):
    s = re.sub(r"[^A-Za-z0-9_]", "_", str(n)).strip("_") or "x"
    if s[0].isdigit():
        s = "x_" + s
    if s.lower() in RESERVED or s.lower() == "target":
        s += "_v"
    base, k = s, 2
    while s in used:
        s = f"{base}_{k}"
        k += 1
    used.add(s)
    return s


def clean(df, target, key):
    log = []
    y = pd.to_numeric(df[target], errors="coerce")
    X = df.drop(columns=[target])
    miss = X.isna().mean()
    drop = list(miss[miss > MAX_MISSING].index)
    if drop:
        log.append(f"dropped {len(drop)} columns with >20% missing")
    X = X.drop(columns=drop)
    keep = y.notna() & X.notna().all(axis=1)
    if (~keep).sum():
        log.append(f"dropped {(~keep).sum()} rows with missing values")
    X, y = X[keep].reset_index(drop=True), y[keep].reset_index(drop=True)
    cols = {}
    for c in X.columns:
        if X[c].dtype == object:
            vc = X[c].astype(str).value_counts()
            if len(vc) > MAX_LEVELS:
                log.append(f"dropped categorical {c} ({len(vc)} levels)")
                continue
            for lev in sorted(vc.index[1:]):
                cols[f"{c}_{lev}"] = (X[c].astype(str) == lev).astype(float)
        else:
            cols[c] = X[c].astype(float)
    X = pd.DataFrame(cols)
    const = [c for c in X.columns if X[c].nunique() <= 1]
    if const:
        log.append(f"dropped {len(const)} constant columns")
    X = X.drop(columns=const)
    if len(X) > MAX_ROWS:
        rng = np.random.default_rng(zlib.crc32(key.encode()) ^ SEED)
        idx = np.sort(rng.choice(len(X), MAX_ROWS, replace=False))
        log.append(f"subsampled {len(X)} -> {MAX_ROWS} rows")
        X, y = X.iloc[idx].reset_index(drop=True), y.iloc[idx].reset_index(drop=True)
    used = set()
    X.columns = [clean_name(c, used) for c in X.columns]
    X["target"] = y.values
    return X, log


# ---------------------------------------------------------------- splits

def upper_split(v, name):
    thr = np.quantile(v, 0.8)
    test = v > thr
    share = test.mean()
    if 0.10 <= share <= 0.30:
        return dict(train=np.flatnonzero(~test), test=np.flatnonzero(test),
                    info=dict(on=name, threshold=float(thr), test_share=float(share)))
    return None


def lower_split(v, name):
    """The mirror of upper_split: train above the 20 % quantile, test at or below it (share 10–30 %)."""
    thr = np.quantile(v, 0.2)
    test = v <= thr
    share = test.mean()
    if 0.10 <= share <= 0.30:
        return dict(train=np.flatnonzero(~test), test=np.flatnonzero(test),
                    info=dict(on=name, threshold=float(thr), test_share=float(share)))
    return None


def lower_splits(t, xfeat_on):
    """xfeat_lo (on the same input as xfeat) and xy_lo (on the target, >= 20 distinct values) — user decision
    03.11.2026; added after the niche registration, so they live beside the older split files."""
    out = {}
    if xfeat_on:
        sp = lower_split(t[xfeat_on].to_numpy(), xfeat_on)
        if sp:
            out["xfeat_lo"] = sp
    y = t["target"].to_numpy()
    if len(np.unique(y)) >= 20:
        sp = lower_split(y, "target")
        if sp:
            out["xy_lo"] = sp
    return out


def make_splits(t):
    X, y = t.drop(columns=["target"]), t["target"].to_numpy()
    n, out = len(t), {}
    for s in (1, 2, 3):
        p = np.random.default_rng(s).permutation(n)
        k = int(round(0.75 * n))
        out[f"iid{s}"] = dict(train=np.sort(p[:k]), test=np.sort(p[k:]), info=dict(seed=s))
    cand = []
    for c in X.columns:
        v = X[c].to_numpy()
        if len(np.unique(v)) >= 20:
            rho = stats.spearmanr(v, y).statistic
            if np.isfinite(rho):
                cand.append((-abs(rho), c, rho))
    for _, c, rho in sorted(cand):
        sp = upper_split(X[c].to_numpy(), c)
        if sp:
            sp["info"]["rho"] = float(rho)
            out["xfeat"] = sp
            break
    sp = upper_split(y, "target") if len(np.unique(y)) >= 20 else None
    if sp:
        out["xy"] = sp
    return out


# ---------------------------------------------------------------- assignment

def assign(keys):
    fam_of = {m: f for f, ms in FAMILIES.items() for m in ms}
    for k in keys:
        fam_of.setdefault(k, k.split(":", 1)[1] if k.startswith("ctr23:") else k)
    ctr_fams = sorted({fam_of[k] for k in keys if k.startswith("ctr23:")})
    perm = np.random.default_rng(SEED).permutation(len(ctr_fams))
    working = {ctr_fams[i] for i in perm[: len(ctr_fams) // 2]}
    side = {}
    for k in keys:
        f = fam_of[k]
        members = [m for m in keys if fam_of[m] == f and m != k]
        if k.startswith("ctr23:"):
            side[k] = ("work" if f in working else "test", f"lottery, family {f}")
        elif k.startswith("grinsztajn:"):
            if f in working:
                side[k] = ("excluded", f"family {f} is on the working side")
            else:
                side[k] = ("test", f"family {f}" if members else "suite")
        else:
            if members:
                side[k] = ("excluded", f"family {f} has a member in another suite")
            else:
                side[k] = ("work", "suite")
    return side, fam_of


def target_check(tables):
    """Pairs across suites whose targets look like the same data and are not in one family."""
    fam = {m: f for f, ms in FAMILIES.items() for m in ms}
    keys = sorted(tables)
    flags = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a.split(":")[0] == b.split(":")[0] or (fam.get(a) and fam.get(a) == fam.get(b)):
                continue
            ya, yb = tables[a]["target"].to_numpy(), tables[b]["target"].to_numpy()
            if stats.ks_2samp(ya, yb).statistic < 0.02:
                flags.append((a, b))
    return flags


def main():
    ctr = {t["name"]: t for t in json.load(open(os.path.join(META, "ctr23_tasks.json")))}
    with open(os.path.join(REPO_DATA, "raw_manifest.tsv")) as f:
        raw = [(r["suite"], r["name"]) for r in csv.DictReader(f, delimiter="\t")]
    os.makedirs(TABLES, exist_ok=True)
    os.makedirs(SPLITS, exist_ok=True)
    tables, logs, shapes = {}, {}, {}
    for suite, name in raw:
        key = f"{suite}:{name}"
        df, target = load(suite, name, ctr)
        shapes[key] = df.shape
        tables[key], logs[key] = clean(df, target, key)
        print(f"{key:40s} {df.shape} -> {tables[key].shape}  {'; '.join(logs[key])}")
    flags = target_check(tables)
    for a, b in flags:
        print("POSSIBLE DUPLICATE (not in FAMILIES):", a, b)
    if flags:
        raise SystemExit("add the pairs above to FAMILIES (or confirm they differ) and rerun")
    side, fam_of = assign(list(tables))
    rows = []
    for key, t in tables.items():
        fn = key.replace(":", "__")
        tpath = os.path.join(TABLES, fn + ".csv")
        t.to_csv(tpath, index=False)
        sp = make_splits(t)
        spath = os.path.join(SPLITS, fn + ".npz")
        np.savez_compressed(spath, **{f"{s}_{part}": v[part] for s, v in sp.items() for part in ("train", "test")})
        info = {s: v["info"] for s, v in sp.items()}
        with open(os.path.join(SPLITS, fn + ".json"), "w") as f:
            json.dump(info, f, indent=1)
        rows.append([key, fam_of[key], side[key][0], side[key][1], shapes[key][0], len(t), t.shape[1] - 1,
                     ",".join(sorted(sp)), info.get("xfeat", {}).get("on", ""), "; ".join(logs[key]),
                     sha256(tpath), sha256(spath)])
    rows.sort(key=lambda r: ({"work": 0, "test": 1, "excluded": 2}[r[2]], r[0].lower()))
    with open(os.path.join(REPO_DATA, "assignment.tsv"), "w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["table", "family", "side", "reason", "rows_raw", "rows", "features", "splits", "xfeat_on",
                    "cleaning", "table_sha256", "splits_sha256"])
        w.writerows(rows)
    for s in ("work", "test", "excluded"):
        print(s, sum(r[2] == s for r in rows))


if __name__ == "__main__":
    main()
