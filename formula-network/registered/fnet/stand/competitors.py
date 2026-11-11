"""After the four registered tests (fnet/README.md 15): competitors the tests did not include, on the same four suites and
splits, as development material (results apart from the registered files).

- pysr: PySR (one formula; + - * / exp log sqrt, size up to 30, 120 s per pair, 4 threads), the symbolic-regression
  reference;
- mlp16, mlp32: small MLPs (two hidden layers of 16 or 32 units), the baseline MLP's pipeline otherwise (standardised
  inputs and target, early stopping); with --c also their C code (size and time per prediction on one split per table,
  as size.py measures the network's), and mlp64, the baseline's size.

    python competitors.py --model pysr|mlp16|mlp32 [--suites niche,fresh,third,fourth]
    python competitors.py --c [--suites ...]
Results: RESULTS/<suite>_competitors_test.tsv and RESULTS/<suite>_competitors_size.tsv (appended, finished rows skipped).
"""
import argparse
import csv
import os
import sys
import time

import numpy as np
import pandas as pd

from common import REPO_DATA, RESULTS, TABLES, load_splits, metrics

SPLITS = {"niche": ["iid1", "time", "xfeat", "xy"]}
DEFAULT_SPLITS = ["iid1", "xfeat", "xy", "xfeat_lo", "xy_lo"]


def keys_of(suite):
    with open(os.path.join(REPO_DATA, f"{suite}_assignment.tsv"), encoding="utf-8") as f:
        return [r["table"] for r in csv.DictReader(f, delimiter="\t") if r["side"] == "test"]


def mlp(h):
    from sklearn.compose import TransformedTargetRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    m = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(h, h), early_stopping=True, max_iter=500,
                                                     random_state=0))
    return TransformedTargetRegressor(regressor=m, transformer=StandardScaler())


def pysr_model(n):
    from pysr import PySRRegressor
    return PySRRegressor(binary_operators=["+", "-", "*", "/"], unary_operators=["exp", "log", "sqrt"], maxsize=30,
                         niterations=1_000_000, timeout_in_seconds=120, random_state=0, progress=False, verbosity=0,
                         batching=n > 5000, temp_equation_file=True, parallelism="multithreading")


def mlp_c(model, V):
    """The fitted pipeline as one C function (double): scale, two ReLU layers, linear output, unscale."""
    pipe = model.regressor_
    sc, net = pipe.named_steps["standardscaler"], pipe.named_steps["mlpregressor"]
    ys = model.transformer_
    fmt = lambda a: ", ".join("%.17g" % v for v in np.ravel(a))
    (W1, W2, W3), (b1, b2, b3) = net.coefs_, net.intercepts_
    H1, H2 = W1.shape[1], W2.shape[1]
    return f"""#include <math.h>
static const double mu[{V}] = {{ {fmt(sc.mean_)} }}, sd[{V}] = {{ {fmt(sc.scale_)} }};
static const double W1[{V}][{H1}] = {{ {fmt(W1)} }}, b1[{H1}] = {{ {fmt(b1)} }};
static const double W2[{H1}][{H2}] = {{ {fmt(W2)} }}, b2[{H2}] = {{ {fmt(b2)} }};
static const double W3[{H2}] = {{ {fmt(W3)} }};
double mlp_predict(const double x[]) {{
    double z[{V}], h1[{H1}], h2[{H2}], s;
    for (int i = 0; i < {V}; ++i) z[i] = (x[i] - mu[i]) / sd[i];
    for (int j = 0; j < {H1}; ++j) {{ s = b1[j]; for (int i = 0; i < {V}; ++i) s += z[i] * W1[i][j]; h1[j] = s > 0 ? s : 0; }}
    for (int j = 0; j < {H2}; ++j) {{ s = b2[j]; for (int i = 0; i < {H1}; ++i) s += h1[i] * W2[i][j]; h2[j] = s > 0 ? s : 0; }}
    s = {float(b3[0]):.17g};
    for (int i = 0; i < {H2}; ++i) s += h2[i] * W3[i];
    return s * {float(ys.scale_[0]):.17g} + {float(ys.mean_[0]):.17g};
}}
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["pysr", "mlp16", "mlp32"])
    ap.add_argument("--c", action="store_true")
    ap.add_argument("--suites", default="niche,fresh,third,fourth")
    a = ap.parse_args()
    for suite in a.suites.split(","):
        if a.c:
            run_c(suite)
            continue
        out = os.path.join(RESULTS, f"{suite}_competitors_test.tsv")
        done = set()
        if os.path.exists(out):
            done = {(r["table"], r["split"], r["model"]) for r in csv.DictReader(open(out, encoding="utf-8"), delimiter="\t")}
        else:
            with open(out, "w", newline="", encoding="utf-8") as f:
                csv.writer(f, delimiter="\t", lineterminator="\n").writerow(
                    ["table", "split", "model", "rmse", "nonfinite", "seconds", "formula"])
        for key in keys_of(suite):
            fn = key.replace(":", "__")
            t = pd.read_csv(os.path.join(TABLES, fn + ".csv"))
            sp, info = load_splits(fn)
            X, y = t.drop(columns=["target"]).to_numpy(dtype=float), t["target"].to_numpy(dtype=float)
            for split in SPLITS.get(suite, DEFAULT_SPLITS):
                if f"{split}_train" not in sp or (key, split, a.model) in done:
                    continue
                tr, te = sp[f"{split}_train"], sp[f"{split}_test"]
                t0 = time.time()
                formula = ""
                try:
                    if a.model == "pysr":
                        m = pysr_model(len(tr)).fit(X[tr], y[tr])
                        p = m.predict(X[te])
                        formula = str(m.sympy())
                    else:
                        m = mlp(int(a.model[3:])).fit(X[tr], y[tr])
                        p = m.predict(X[te])
                except Exception as e:                       # a failed fit counts as the training mean
                    p = np.full(len(te), np.nan)
                    formula = f"error: {e}"[:200]
                _, rmse, bad = metrics(y[te], p, y[tr].mean())
                with open(out, "a", newline="", encoding="utf-8") as f:
                    csv.writer(f, delimiter="\t", lineterminator="\n").writerow(
                        [key, split, a.model, repr(rmse), bad, round(time.time() - t0, 1), formula])
                print(f"{key:36s} {split:9s} {a.model}  rmse {rmse:.4g}  {time.time() - t0:.0f}s", flush=True)


def run_c(suite):
    from size import compile_and_measure, read_numbers  # noqa: F401  (the same measurement as the network's)
    out = os.path.join(RESULTS, f"{suite}_competitors_size.tsv")
    work = os.path.join(RESULTS, f"{suite}_competitors_size")
    os.makedirs(work, exist_ok=True)
    rows = []
    for key in keys_of(suite):
        fn = key.replace(":", "__")
        t = pd.read_csv(os.path.join(TABLES, fn + ".csv"))
        sp, info = load_splits(fn)
        split = "iid1" if "iid1" in info else "time"
        tr, te = sp[f"{split}_train"], sp[f"{split}_test"]
        X, y = t.drop(columns=["target"]).to_numpy(dtype=float), t["target"].to_numpy(dtype=float)
        for h in (16, 32, 64):
            m = mlp(h).fit(X[tr], y[tr])
            d = os.path.join(work, f"{fn}_mlp{h}")
            os.makedirs(d, exist_ok=True)
            nb, ns, pc = compile_and_measure(d, mlp_c(m, X.shape[1]), "mlp_predict", X[te], 200)
            diff = float(np.nanmax(np.abs(pc - m.predict(X[te]))))
            rows.append([key, split, f"mlp{h}", nb, ns, diff])
            print(f"{key:36s} mlp{h}: {nb} B {ns:.1f} ns  C vs sklearn {diff:.2g}", flush=True)
    pd.DataFrame(rows, columns=["table", "split", "model", "bytes", "ns", "c_check"]).to_csv(out, sep="\t", index=False)


if __name__ == "__main__":
    main()
