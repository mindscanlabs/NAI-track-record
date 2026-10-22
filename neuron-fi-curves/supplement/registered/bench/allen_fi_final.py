"""
f–I curves (IDEAS §18, task 4): the registered checks (docs/prereg/ALLEN_FI.md), on the test cells or, with
--explore --cut K, on the working part's own split. Uses bench/allen_fi.py's rows.

    python bench/allen_fi_final.py ktable [--explore --cut K]       the per-cell k of f = k ln x → ktrain.csv, kpoints.csv
    (NAI: --data ktrain.csv --predict kpoints.csv nai_k.pred)
    python bench/allen_fi_final.py score  [--explore --cut K]

Checks, cells with ≥ 7 suprathreshold points:
  A. continuation: each cell's lower 60 % of currents fitted, its upper 40 % predicted, per-cell forms —
     linear a + b·x; ln a + b·ln x; k·ln x; a + b·ln(x − c); a − b·exp(−x/c); a + b·√(x − 1); a + b(x − 1)^p.
  B. the whole curve from the rheobase and one sweep (nearest x = 2, x > 1.2): k·ln x with k = f1/ln x1,
     against the line through the threshold, f1·(x − 1)/(x1 − 1).
  C. where the log law's zero sits: x0 = exp(−a/b) of a + b·ln x fitted to the whole curve of each cell.
  D. k from the cell's features (tau, Ri, Ith, spiny, human): NAI's law against the log-linear one; the
     whole curve with no sweep above the rheobase.
Error: |log10(f_pred/f)|, a prediction below 0.5 Hz counted as 0.5 Hz.
"""
import argparse, importlib.util, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("af", os.path.join(HERE, "allen_fi.py"))
af = importlib.util.module_from_spec(spec)
spec.loader.exec_module(af)
X = ["tau", "Ri", "Ith", "spiny", "human"]


def err(p, f):
    return abs(math.log10(max(p, 0.5) / f)) if p == p else 3.0


def kcells(rows):
    out = []
    for cid, rs in sorted(af.cell_rows(rows).items()):
        lx = [math.log(r["x"]) for r in rs]
        k = sum(l * r["f"] for l, r in zip(lx, rs)) / max(1e-12, sum(l * l for l in lx))
        if k > 0:
            r0 = rs[0]
            out.append(dict(cell=cid, lgk=math.log10(k), tau=r0["tau"], Ri=r0["Ri"], Ith=r0["I"] / r0["x"],
                            spiny=r0["spiny"], human=r0["human"], rows=rs))
    return out


def loglin(tr):
    c = af.lsq([[1] + [math.log10(r[k]) for k in X[:3]] + [r["spiny"], r["human"]] for r in tr], [r["lgk"] for r in tr])
    return c, (lambda r: c[0] + sum(c[i + 1] * math.log10(r[k]) for i, k in enumerate(X[:3])) + c[4] * r["spiny"] + c[5] * r["human"])


def ktable(a, out):
    fit, chk = af.load(a)
    tr, ch = kcells(fit), kcells(chk)
    _, base = loglin(tr)
    sig = math.sqrt(statistics.mean((r["lgk"] - base(r)) ** 2 for r in tr))
    with open(os.path.join(out, "ktrain.csv"), "w", encoding="utf-8") as fh:
        fh.write(",".join(X + ["lgk", "sigma"]) + "\n")
        for r in tr:
            fh.write(",".join("%.17g" % r[k] for k in X) + ",%.17g,%.4f\n" % (r["lgk"], sig))
    with open(os.path.join(out, "kpoints.csv"), "w", encoding="utf-8") as fh:
        fh.write(",".join(X + ["lgk"]) + "\n")
        for r in ch:
            fh.write(",".join("%.17g" % r[k] for k in X) + ",0\n")
    print("k table: fitted cells %d, checked %d, sigma %.4f" % (len(tr), len(ch), sig))


def fit3(rs, g, grid):
    best = None
    for p in grid:
        try:
            c = af.lsq([[1, g(r["x"], p)] for r in rs], [r["f"] for r in rs])
        except (ZeroDivisionError, ValueError):
            continue
        e = sum((c[0] + c[1] * g(r["x"], p) - r["f"]) ** 2 for r in rs)
        if best is None or e < best[0]:
            best = (e, p, c)
    _, p, c = best
    return lambda x: c[0] + c[1] * g(x, p)


def per_cell(rs, kind):
    if kind == "linear":
        c = af.lsq([[1, r["x"]] for r in rs], [r["f"] for r in rs]); return lambda x: c[0] + c[1] * x
    if kind == "ln":
        c = af.lsq([[1, math.log(r["x"])] for r in rs], [r["f"] for r in rs]); return lambda x: c[0] + c[1] * math.log(x)
    if kind == "k ln":
        lx = [math.log(r["x"]) for r in rs]
        k = sum(l * r["f"] for l, r in zip(lx, rs)) / max(1e-12, sum(l * l for l in lx)); return lambda x: k * math.log(x)
    if kind == "ln(x-c)":
        return fit3(rs, lambda x, p: math.log(x - p), [k / 40 for k in range(0, 39)])
    if kind == "exp-sat":
        return fit3(rs, lambda x, p: -math.exp(-x / p), [k / 4 for k in range(1, 81)])
    if kind == "sqrt":
        c = af.lsq([[1, math.sqrt(r["x"] - 1)] for r in rs], [r["f"] for r in rs]); return lambda x: c[0] + c[1] * math.sqrt(x - 1)
    if kind == "power3":
        return fit3(rs, lambda x, p: (x - 1) ** p, [k / 20 for k in range(2, 41)])
    raise ValueError(kind)


def score(a, out):
    fit, chk = af.load(a)
    cc = af.cell_rows(chk)
    res = {"cells": len(cc)}
    # A
    A = {}
    for kind in ("linear", "ln", "k ln", "ln(x-c)", "exp-sat", "sqrt", "power3"):
        e = []
        for cid, rs in cc.items():
            k = max(3, int(round(0.6 * len(rs))))
            f = per_cell(rs[:k], kind)
            e += [err(f(r["x"]), r["f"]) for r in rs[k:]]
        e.sort()
        A[kind] = (statistics.mean(e), statistics.median(e), len(e))
    res["A"] = A
    # B
    B = {"k ln x": [], "line through threshold": []}
    for cid, rs in cc.items():
        cand = [r for r in rs if r["x"] > 1.2]
        if not cand:
            continue
        r1 = min(cand, key=lambda r: abs(r["x"] - 2))
        k = r1["f"] / math.log(r1["x"])
        for r in rs:
            if r is not r1:
                B["k ln x"].append(err(k * math.log(r["x"]), r["f"]))
                B["line through threshold"].append(err(r1["f"] * (r["x"] - 1) / (r1["x"] - 1), r["f"]))
    res["B"] = {k: (statistics.mean(v), statistics.median(v), len(v)) for k, v in B.items()}
    # C
    x0 = []
    for cid, rs in cc.items():
        c = af.lsq([[1, math.log(r["x"])] for r in rs], [r["f"] for r in rs])
        if c[1] > 0:
            x0.append(math.exp(-c[0] / c[1]))
    x0.sort()
    res["C"] = (statistics.median(x0), x0[len(x0) // 4], x0[3 * len(x0) // 4], len(x0))
    # D
    tr, ch = kcells(fit), kcells(chk)
    c, base = loglin(tr)
    D = {"log-linear": [base(r) for r in ch]}
    pf = os.path.join(out, "nai_k.pred")
    if os.path.exists(pf):
        v = [float(l) for l in open(pf) if l.strip()]
        if len(v) == len(ch):
            D["NAI"] = v
    res["D"] = {}
    for k, v in D.items():
        ek = [abs(p - r["lgk"]) for p, r in zip(v, ch)]
        ef = [err(10 ** p * math.log(q["x"]), q["f"]) for p, r in zip(v, ch) for q in r["rows"] if q["x"] > 1]
        res["D"][k] = (statistics.mean(ek), statistics.mean(ef), statistics.median(ef), len(ch))
    res["D_loglin"] = c
    print("cells with >= 7 points: %d" % len(cc))
    print("A. continuation (upper 40 %% from lower 60 %%), |lg f_pred/f|: mean / median (rows)")
    for k, v in A.items():
        print("   %-10s %.4f / %.4f (%d)" % (k, v[0], v[1], v[2]))
    print("B. whole curve from the rheobase and one sweep: mean / median (rows)")
    for k, v in res["B"].items():
        print("   %-24s %.4f / %.4f (%d)" % (k, v[0], v[1], v[2]))
    print("C. x0 of a + b ln x: median %.3f, quartiles %.3f-%.3f (%d cells)" % res["C"])
    print("D. k from features: |d lg k| mean; whole curve with no sweep: mean / median")
    for k, v in res["D"].items():
        print("   %-12s %.4f   %.4f / %.4f (%d cells)" % (k, v[0], v[1], v[2], v[3]))
    json.dump(res, open(os.path.join(out, "final_score.json"), "w"), indent=1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ktable", "score"])
    ap.add_argument("--explore", action="store_true")
    ap.add_argument("--cut", type=int, default=1)
    a = ap.parse_args()
    a.out = af.DATA
    out = os.path.join(af.OUT, "explore", "cut%d" % a.cut) if a.explore else os.path.join(af.OUT, "final")
    os.makedirs(out, exist_ok=True)
    {"ktable": ktable, "score": score}[a.cmd](a, out)


if __name__ == "__main__":
    main()
