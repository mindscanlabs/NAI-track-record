"""NASA Common Research Model (a generic wide-body transport), National Transonic Facility Test 197 (2010), the data
posted at commonresearchmodel.larc.nasa.gov (NTF197Data.zip, TWICSCorr: wall-interference corrected) -> one table
of the wing-body-tail configuration for models of CL, CD and CM. A US Government work; no NASA endorsement implied.

Rules, fixed before any model was run:
- rows: CONFIG = 3 (wing-body-tail; AIAA 2010-4218) with tail incidence CONFT in {-2, 0, +2};
- inputs: AWALL (corrected angle of attack, deg), MWALL (corrected Mach), CREYN (Reynolds number, millions), QINFFT
  (dynamic pressure; the wing's elastic deflection), CONFT (tail incidence, deg); targets: CLWALL, CDWALL, CMWALL;
- sides, by whole runs (an alpha sweep each): test_edge = runs at nominal Mach 0.86 and above (the drag rise, beyond
  the training range); test_inside = every 5th run, in order of run number, among runs at nominal Mach 0.85 and
  below; train = the other runs.
    python -s -E aircraft_prepare.py      # D:/Claude/nai-data/fnet/aircraft/tables/crm_wbt.csv, MANIFEST.tsv
"""
import hashlib
import io
import os
import zipfile

import pandas as pd

RAW = "D:/Claude/nai-data/fnet/aircraft/raw/NTF197Data.zip"
OUT = "D:/Claude/nai-data/fnet/aircraft/tables"
INPUTS = ["AWALL", "MWALL", "CREYN", "QINFFT", "CONFT"]
TARGETS = ["CLWALL", "CDWALL", "CMWALL"]


def main():
    os.makedirs(OUT, exist_ok=True)
    z = zipfile.ZipFile(RAW)
    parts = []
    for n in sorted(z.namelist()):
        if n.startswith("TWICSCorr/") and n.lower().endswith(".csv"):
            d = pd.read_csv(io.BytesIO(z.read(n)))
            parts.append(d[["RUN", "POINT", "MACH", "CONFIG"] + INPUTS + TARGETS])
    d = pd.concat(parts, ignore_index=True)
    d = d[(d.CONFIG == 3) & d.CONFT.isin([-2, 0, 2])].dropna(subset=INPUTS + TARGETS).copy()
    d["mach_nom"] = d.MACH.round(2)
    runs = d.groupby("RUN").mach_nom.first().sort_index()
    edge = set(runs[runs >= 0.86].index)
    low = [r for r in runs.index if r not in edge]
    inside = set(low[4::5])
    d["side"] = ["test_edge" if r in edge else "test_inside" if r in inside else "train" for r in d.RUN]
    path = f"{OUT}/crm_wbt.csv"
    d[["RUN", "POINT", "side", "mach_nom"] + INPUTS + TARGETS].to_csv(path, index=False, float_format="%.8g")
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    with open(f"{OUT}/MANIFEST.tsv", "w", newline="\n") as f:
        f.write(f"file\tsha256\nPoints by side\t{d.side.value_counts().to_dict()}\ncrm_wbt.csv\t{h}\n")
    print(d.groupby("side").agg(points=("RUN", "size"), runs=("RUN", "nunique"), mach_min=("mach_nom", "min"),
                                mach_max=("mach_nom", "max")))
    print(d.groupby(["side", "CREYN"]).size().unstack(fill_value=0).round(0))
    print("CONFT by side:", d.groupby(["side", "CONFT"]).size().to_dict())


if __name__ == "__main__":
    main()
