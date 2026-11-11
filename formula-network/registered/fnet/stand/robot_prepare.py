"""Panda real-robot inverse dynamics (Zenodo 12516500, MERL, CC BY-SA 4.0) -> CSV tables for fnet.

The archive holds pickles (pandas DataFrames, numpy arrays). Unpickling runs code, so a restricted unpickler
accepts only the classes these files were seen to name (pickletools listing, 2026-11-08); anything else stops.

    python -I robot_prepare.py            # D:/Claude/nai-data/fnet/robot/{tables,baselines}
"""
import hashlib
import io
import os
import pickle
import re
import sys
import zipfile

import numpy as np

ZIP = "D:/Claude/nai-data/fnet/niche/raw/melfa.zip"
OUT = "D:/Claude/nai-data/fnet/robot"
EXP = "Data/Robots/PANDA/Experiments/"
RES = "Data/Robots/PANDA/Results/"

ALLOWED = {
    ("pandas.core.frame", "DataFrame"),
    ("pandas.core.internals.managers", "BlockManager"),
    ("pandas.core.internals.blocks", "new_block"),
    ("pandas.core.indexes.base", "_new_Index"),
    ("pandas.core.indexes.base", "Index"),
    ("pandas.core.indexes.range", "RangeIndex"),
    ("functools", "partial"),
    ("builtins", "slice"),
    ("numpy", "ndarray"),
    ("numpy", "dtype"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy.core.multiarray", "scalar"),
    ("numpy._core.multiarray", "_reconstruct"),
    ("numpy._core.multiarray", "scalar"),
}


class _State:
    """Stands for a pandas object: keeps what unpickling hands it, runs no pandas code."""
    def __init__(self, *a, **k):
        self.args, self.kwargs, self.state = a, k, None

    def __setstate__(self, s):
        self.state = s


class FrameStub(_State):
    pass


class ManagerStub(_State):
    pass


class RangeStub(_State):
    pass


def new_block_stub(values, placement=None, ndim=None, **_):
    return ("block", values, placement)


def new_index_stub(cls, d):
    if cls is RangeStub:
        return np.arange(d.get("start", 0), d["stop"], d.get("step", 1))
    return np.asarray(d["data"])


STUBS = {
    ("pandas.core.frame", "DataFrame"): FrameStub,
    ("pandas.core.internals.managers", "BlockManager"): ManagerStub,
    ("pandas.core.internals.blocks", "new_block"): new_block_stub,
    ("pandas.core.indexes.base", "_new_Index"): new_index_stub,
    ("pandas.core.indexes.base", "Index"): _State,
    ("pandas.core.indexes.range", "RangeIndex"): RangeStub,
}


class Restricted(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) not in ALLOWED:
            raise pickle.UnpicklingError(f"refused: {module}.{name}")
        if (module, name) in STUBS:
            return STUBS[(module, name)]
        if module == "numpy.core.multiarray":
            module = "numpy._core.multiarray"
        return super().find_class(module, name)


class Frame:
    """The columns of an unpickled DataFrame: {name: 1-D array}."""
    def __init__(self, stub):
        st = stub.state
        mgr = st["_mgr"] if isinstance(st, dict) else st
        ms = mgr.state
        if ms is None and len(mgr.args) == 2:
            # pandas 2.x: BlockManager(blocks, axes), each block ("block", values, placement)
            blocks, axes = mgr.args
            items = np.asarray(axes[0])
            self.cols = {}
            for _, vals, loc in blocks:
                vals = np.asarray(vals)
                idx = np.arange(len(items))[loc] if isinstance(loc, slice) else np.asarray(loc)
                for k, i in enumerate(idx):
                    self.cols[str(items[i])] = vals[k]
            return
        # pandas >= 1.x BlockManager state: (axes, blocks, ...) or a dict with "0.14.1" layout
        if isinstance(ms, tuple) and len(ms) >= 4 and isinstance(ms[3], dict):
            info = ms[3]["0.14.1"]
            axes, blocks = info["axes"], info["blocks"]
            items = np.asarray(axes[0])
            self.cols = {}
            for b in blocks:
                vals, loc = np.asarray(b["values"]), b["mgr_locs"]
                idx = np.arange(len(items))[loc] if isinstance(loc, slice) else np.asarray(loc)
                for k, i in enumerate(idx):
                    self.cols[str(items[i])] = vals[k]
            return
        raise ValueError(f"unknown BlockManager state: {type(ms)} {str(ms)[:200]}")

    @property
    def columns(self):
        return list(self.cols)

    def matrix(self, names):
        return np.column_stack([np.asarray(self.cols[c], dtype=np.float64) for c in names])


def load(z, member):
    obj = Restricted(io.BytesIO(z.read(member))).load()
    return Frame(obj) if isinstance(obj, FrameStub) else obj


def main():
    z = zipfile.ZipFile(ZIP)
    names = z.namelist()
    os.makedirs(OUT + "/tables", exist_ok=True)
    os.makedirs(OUT + "/baselines", exist_ok=True)
    pat = re.compile(r"panda7dof_num_sin_(\d+)_seed_(\d+)_as_filtered_fcut4\.0\.pkl$")
    manifest = []
    for n in sorted(names):
        m = pat.search(n)
        if not m or not n.startswith(EXP):
            continue
        nsin, seed = int(m.group(1)), int(m.group(2))
        df = load(z, n)
        cols = [c for c in df.columns]
        need = [f"{k}_{j}" for k in ("q", "dq", "ddq", "tau", "tau_interp") for j in range(1, 8)]
        miss = [c for c in need if c not in cols]
        if miss:
            print("missing columns", n, miss, file=sys.stderr)
            sys.exit(1)
        a = df.matrix(need)
        t = df.matrix(["t"])[:, 0] if "t" in cols else np.arange(len(a), dtype=np.float64)
        path = f"{OUT}/tables/panda_seed{seed:02d}.csv"
        with open(path, "w", newline="\n") as f:
            f.write("t," + ",".join(need) + "\n")
            for i in range(len(a)):
                f.write(repr(float(t[i])) + "," + ",".join(repr(float(v)) for v in a[i]) + "\n")
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        dt = np.median(np.diff(t)) if len(t) > 1 else float("nan")
        manifest.append((seed, nsin, len(a), float(dt), h))
        print(f"seed {seed:2d} num_sin {nsin:3d} rows {len(a):6d} dt {dt:.4g} extra cols {sorted(set(cols) - set(need))}")
    with open(OUT + "/tables/MANIFEST.tsv", "w", newline="\n") as f:
        f.write("seed\tnum_sin\trows\tdt\tsha256\n")
        for r in manifest:
            f.write("\t".join(str(x) for x in r) + "\n")

    # The authors' estimates on the test trajectories: Y (measured, filtered) and Y_hat per model, comb, seed.
    rp = re.compile(r"50-100-sin_two-dataset_comb(\d+)_(.+?)_panda7dof_num_sin_100_seed_(\d+)_as_filtered_fcut4\.0_estimates\.pkl$")
    rows = 0
    with open(OUT + "/baselines/estimates_index.tsv", "w", newline="\n") as idx:
        idx.write("comb\tmodel\tseed\tfile\n")
        for n in sorted(names):
            m = rp.search(n)
            if not m or not n.startswith(RES):
                continue
            comb, model, seed = int(m.group(1)), m.group(2), int(m.group(3))
            obj = load(z, n)
            d = obj if isinstance(obj, dict) else (obj[-1] if isinstance(obj, list) and isinstance(obj[-1], dict) else obj[0])
            if isinstance(obj, list) and len(obj) == 2 and all(isinstance(x, dict) for x in obj):
                d = obj[1]   # m_ind_*: [train estimates, test estimates]
            y, yh = np.asarray(d["Y"], dtype=np.float64), np.asarray(d["Y_hat"], dtype=np.float64)
            if y.shape[0] != 7:
                y, yh = y.T, yh.T
            fn = f"comb{comb:02d}__{model}__seed{seed:02d}.npz"
            np.savez(f"{OUT}/baselines/{fn}", Y=y, Y_hat=yh)
            idx.write(f"{comb}\t{model}\t{seed}\t{fn}\n")
            rows += 1
    print("baseline estimate files:", rows)


if __name__ == "__main__":
    main()
