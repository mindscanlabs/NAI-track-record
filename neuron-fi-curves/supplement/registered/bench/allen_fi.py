"""
f–I curves of the Allen Cell Types Database (IDEAS §18, task 4; docs/ALLEN_FI.md).

    python bench/allen_fi.py fetch [--out D:/Claude/nai-data/allen_ct]
    python bench/allen_fi.py split --table T [--explore --cut 1|2]
    python bench/allen_fi.py run   --table T --tag NAME [--cli ...] [--seconds 300] [--nai "..."] [--explore --cut K]
    python bench/allen_fi.py score [--explore --cut K]

fetch: every cell's details (ApiCellTypesSpecimenDetail: species, layer, dendrite type, Cre line,
the cell-level electrophysiology features) and every Long Square sweep (EphysSweep: the current's
amplitude in pA, its duration, the number of spikes), page by page from the public API
(api.brain-map.org, RMA queries). No NWB files. Standard library only.

The rows: one per cell and current amplitude at or above the cell's rheobase (ef__threshold_i_long_square)
with spikes; f = spikes / duration (Hz), averaged over repeats. Test: 30 % of the cells (seed 20261022),
never read by --explore; exploration splits the working cells again (seed --cut, 30 % checked).

Tables (the value is log10 f; sigma: the RMS of the baseline power law's residuals on the rows fitted):
  x    — x = I/I_th, tau (ms)
  xr   — x, tau, Ri (MΩ)
  xrc  — x, tau, Ri, spiny (1 spiny or sparsely spiny, 0 aspiny), human (1, 0 mouse)
Baselines (least squares in logs on the rows fitted): LIF, f = 1/(t_ref + tau·ln(x/(x − 1))), t_ref fitted;
a power law A·(x − 1 + 0.05)^b; the same times tau^c; and with the class terms.
"""
import argparse, collections, csv, datetime, glob, hashlib, json, math, os, random, statistics, subprocess, sys, time
import urllib.parse, urllib.request

API = "https://api.brain-map.org/api/v2/data/query.json"
DATA = "D:/Claude/nai-data/allen_ct"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "allen_fi")
SEED_TEST = 20261022
TABLES = {"x": ["x", "tau"], "xr": ["x", "tau", "Ri"], "xrc": ["x", "tau", "Ri", "spiny", "human"]}


def rma(criteria, page=2000, order="id"):
    rows, start = [], 0
    while True:
        q = criteria + ",rma::options[num_rows$eq%d][start_row$eq%d][order$eq'%s']" % (page, start, order)
        url = API + "?" + urllib.parse.urlencode({"criteria": q})
        for attempt in range(5):
            try:
                d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nai-bench/1.0"}),
                                                      timeout=300).read().decode("utf-8"))
                break
            except Exception as e:
                if attempt == 4:
                    raise
                print("  retry:", e, flush=True)
                time.sleep(5 * (attempt + 1))
        if not d.get("success"):
            raise RuntimeError(str(d)[:300])
        rows += d["msg"]
        start += len(d["msg"])
        print("  %d of %d" % (start, d["total_rows"]), flush=True)
        if start >= d["total_rows"] or not d["msg"]:
            return rows


def fetch(a):
    os.makedirs(a.out, exist_ok=True)
    t = datetime.datetime.now(datetime.timezone.utc)
    cells = rma("model::ApiCellTypesSpecimenDetail", order="specimen__id")
    json.dump(cells, open(os.path.join(a.out, "cells.json"), "w", encoding="utf-8"))
    sweeps = rma("model::EphysSweep,rma::criteria,[stimulus_name$eq'Long Square']", page=5000)
    keep = ("specimen_id", "sweep_number", "stimulus_absolute_amplitude", "stimulus_duration", "num_spikes", "stimulus_units")
    json.dump([{k: s.get(k) for k in keep} for s in sweeps], open(os.path.join(a.out, "sweeps.json"), "w", encoding="utf-8"))
    man = {"taken_utc": t.isoformat(), "source": API, "cells": len(cells), "sweeps": len(sweeps),
           "sha256": {f: hashlib.sha256(open(os.path.join(a.out, f), "rb").read()).hexdigest() for f in ("cells.json", "sweeps.json")}}
    json.dump(man, open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(man, indent=1))


# ---- rows -------------------------------------------------------------------------------------

def load(a):
    cells = {c["specimen__id"]: c for c in json.load(open(os.path.join(a.out, "cells.json"), encoding="utf-8"))}
    sweeps = json.load(open(os.path.join(a.out, "sweeps.json"), encoding="utf-8"))
    ids = sorted(cells)
    test = set(random.Random(SEED_TEST).sample(ids, round(0.3 * len(ids))))
    work = [i for i in ids if i not in test]
    if a.explore:
        check = set(random.Random(a.cut).sample(work, round(0.3 * len(work))))
        fit, chk = [i for i in work if i not in check], [i for i in work if i in check]
    else:
        fit, chk = work, [i for i in ids if i in test]
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    want = set(fit) | set(chk)
    for s in sweeps:
        amp, dur = s["stimulus_absolute_amplitude"], s["stimulus_duration"]
        if s["specimen_id"] in want and amp is not None and dur and dur > 0 and amp > 0:
            by[s["specimen_id"]][round(amp, 3)].append((s["num_spikes"] or 0) / dur)

    def rows(ids_):
        out = []
        for i in ids_:
            c = cells[i]
            ith, tau, ri = c["ef__threshold_i_long_square"], c["ef__tau"], c["ef__ri"]
            if not ith or not tau or not ri or ith <= 0 or tau <= 0 or ri <= 0 or i not in by:
                continue
            for amp, v in sorted(by[i].items()):
                f = statistics.mean(v)
                if amp >= ith and f > 0:
                    out.append(dict(cell=i, x=amp / ith, I=amp, f=f, tau=tau, Ri=ri,
                                    spiny=0 if c["tag__dendrite_type"] == "aspiny" else 1,
                                    human=1 if c["donor__species"] == "Homo Sapiens" else 0))
        return out
    return rows(fit), rows(chk)


def lsq(A, y):
    n = len(A[0])
    G = [[sum(r[i] * r[j] for r in A) for j in range(n)] for i in range(n)]
    h = [sum(r[i] * v for r, v in zip(A, y)) for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(G[k][i]))
        G[i], G[p], h[i], h[p] = G[p], G[i], h[p], h[i]
        for k in range(i + 1, n):
            m = G[k][i] / G[i][i]
            for c in range(i, n):
                G[k][c] -= m * G[i][c]
            h[k] -= m * h[i]
    c = [0.0] * n
    for i in reversed(range(n)):
        c[i] = (h[i] - sum(G[i][j] * c[j] for j in range(i + 1, n))) / G[i][i]
    return c


def baselines(fit):
    lx = lambda r: math.log10(r["x"] - 1 + 0.05)
    lf = [math.log10(r["f"]) for r in fit]
    out = {}
    best = None
    for k in range(0, 80):
        t = k * 0.0005
        e = [abs(math.log10((1.0 / (t + r["tau"] / 1000 * math.log(r["x"] / (r["x"] - 1))) if r["x"] > 1 else 1e-3) / r["f"]))
             for r in fit]
        if best is None or statistics.mean(e) < best[0]:
            best = (statistics.mean(e), t)
    t = best[1]
    out["LIF (t_ref %.4f s)" % t] = lambda r, t=t: math.log10(1.0 / (t + r["tau"] / 1000 * math.log(r["x"] / (r["x"] - 1)))) if r["x"] > 1 else -3.0
    c = lsq([[1, lx(r)] for r in fit], lf)
    out["power A(x-1+0.05)^b"] = lambda r, c=c: c[0] + c[1] * lx(r)
    c = lsq([[1, lx(r), math.log10(r["tau"])] for r in fit], lf)
    out["power, tau^c"] = lambda r, c=c: c[0] + c[1] * lx(r) + c[2] * math.log10(r["tau"])
    c = lsq([[1, lx(r), math.log10(r["tau"]), math.log10(r["Ri"]), r["spiny"], r["human"]] for r in fit], lf)
    out["power, tau, Ri, class"] = lambda r, c=c: c[0] + c[1] * lx(r) + c[2] * math.log10(r["tau"]) + c[3] * math.log10(r["Ri"]) + c[4] * r["spiny"] + c[5] * r["human"]
    return out


def split(a):
    fit, chk = load(a)
    os.makedirs(OUT, exist_ok=True)
    base = baselines(fit)["power A(x-1+0.05)^b"]
    sig = math.sqrt(statistics.mean((math.log10(r["f"]) - base(r)) ** 2 for r in fit))
    xs = TABLES[a.table]
    with open(os.path.join(OUT, "train_%s.csv" % a.table), "w", newline="", encoding="utf-8") as fh:
        fh.write("# Allen Cell Types, Long Square: x = I/I_th, tau (ms), Ri (MOhm); lgf = log10 rate (Hz)\n")
        fh.write(",".join(xs + ["lgf", "sigma"]) + "\n")
        for r in fit:
            fh.write(",".join("%.17g" % r[k] for k in xs) + ",%.17g,%.4f\n" % (math.log10(r["f"]), sig))
    with open(os.path.join(OUT, "points_%s.csv" % a.table), "w", newline="", encoding="utf-8") as fh:
        fh.write(",".join(xs + ["lgf"]) + "\n")
        for r in chk:
            fh.write(",".join("%.17g" % r[k] for k in xs) + ",0\n")
    print("%s: rows fitted %d (cells %d), checked %d (cells %d); sigma %.4f" %
          (a.table, len(fit), len(set(r["cell"] for r in fit)), len(chk), len(set(r["cell"] for r in chk)), sig))


def run(a):
    cli = os.path.abspath(a.cli)
    tag = a.tag or a.table
    cmd = [cli, "--data", os.path.join(OUT, "train_%s.csv" % a.table), "--seconds", str(a.seconds), "--seed", "1",
           "--predict", os.path.join(OUT, "points_%s.csv" % a.table), os.path.join(OUT, "nai_%s.pred" % tag)] + a.nai.split()
    out = subprocess.run(cmd, capture_output=True, timeout=20 * a.seconds + 900).stdout.decode("utf-8", "replace")
    open(os.path.join(OUT, "nai_%s.log" % tag), "w", encoding="utf-8").write(out)
    json.dump({"table": a.table, "nai": a.nai, "seconds": a.seconds}, open(os.path.join(OUT, "nai_%s.meta" % tag), "w", encoding="utf-8"))
    best = [l for l in out.splitlines() if l.startswith(("ПРИБЛИЖЕНИЕ", "ЗАКОН", "В ПРЕДЕЛАХ", "РЕШЕНО", "APPROX", "WITHIN", "SOLVED"))]
    print("%s: %s" % (tag, best[-1] if best else "no answer"), flush=True)


def score(a):
    fit, chk = load(a)
    preds = {k: [f(r) for r in chk] for k, f in baselines(fit).items()}
    for mf in sorted(glob.glob(os.path.join(OUT, "nai_*.meta"))):
        tag = os.path.basename(mf)[4:-5]
        pf = os.path.join(OUT, "nai_%s.pred" % tag)
        v = [float(l) for l in open(pf) if l.strip()] if os.path.exists(pf) else []
        preds["NAI " + tag] = v if len(v) == len(chk) else [None] * len(chk)
    print("checked on %d rows of %d cells; error |log10(f_pred/f)|" % (len(chk), len(set(r["cell"] for r in chk))))
    print("%-30s %8s %8s   %8s %8s %8s" % ("", "mean", "median", "x<1.5", "1.5-3", "x>=3"))
    for k, v in preds.items():
        e = [abs(p - math.log10(r["f"])) if p is not None and math.isfinite(p) else 3.0 for p, r in zip(v, chk)]
        by = [[x for x, r in zip(e, chk) if lo <= r["x"] < hi] for lo, hi in ((0, 1.5), (1.5, 3), (3, 1e9))]
        print("%-30s %8.4f %8.4f   %8.4f %8.4f %8.4f" % (k, statistics.mean(e), statistics.median(e), *[statistics.mean(b) for b in by]))


# ---- the shape: one form for every cell, its numbers per cell ------------------------------------
# One table of many cells pools the scatter between cells (σ ≈ 0.5 dex), within which nearly any
# formula passes. Here each cell is a group (Groups.cpp): one form, its constants per cell; the noise
# is the cell's own, the count's: σ(lg f) = 1/(ln 10·√n), n spikes in the second.
#   shape-split: S cells of the rows fitted (seed --cut + 100, ≥ MINPTS points) → shape_train.csv; every
#     checked cell with ≥ MINPTS points: its lower 60 % of currents → shape_cal.csv, the upper 40 % →
#     shape_pts.csv (and their truth).
#   shape-run: NAI's group mode on shape_train.csv (--forms); the chosen form alone (--candidates-in) on
#     shape_cal.csv, predicting shape_pts.csv: the form's numbers fitted on a cell's first sweeps, its curve
#     continued.
#   shape-score: against per-cell baselines fitted on the same first sweeps.
MINPTS = 7


def cell_rows(rows):
    by = collections.defaultdict(list)
    for r in rows:
        by[r["cell"]].append(r)
    return {c: sorted(v, key=lambda r: r["x"]) for c, v in by.items() if len(v) >= MINPTS}


def sig_lg(r):
    n = max(1.0, r["f"])                       # spikes in the 1 s pulse
    return 1.0 / (math.log(10) * math.sqrt(n))


def write_group(path, rows, with_value=True, target="lgf"):
    """target lgf: log10 f, sigma 1/(ln 10·√n); f: the rate itself, sigma √n (a count in 1 s)."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fh.write(("x,%s,sigma,group\n" if with_value else "x,%s,group\n") % target)
        for r in rows:
            if with_value and target == "lgf":
                fh.write("%.17g,%.17g,%.4f,c%d\n" % (r["x"], math.log10(r["f"]), sig_lg(r), r["cell"]))
            elif with_value:
                fh.write("%.17g,%.17g,%.4f,c%d\n" % (r["x"], r["f"], math.sqrt(max(1.0, r["f"])), r["cell"]))
            else:
                fh.write("%.17g,0,c%d\n" % (r["x"], r["cell"]))


def shape_parts(a):
    fit, chk = load(a)
    fc, cc = cell_rows(fit), cell_rows(chk)
    pick = sorted(random.Random(a.cut + 100).sample(sorted(fc), min(a.cells, len(fc))))
    cal, pts = [], []
    for c, rs in sorted(cc.items()):
        k = max(3, int(round(0.6 * len(rs))))
        cal += rs[:k]
        pts += rs[k:]
    return [r for c in pick for r in fc[c]], cal, pts


def shape_split(a):
    train, cal, pts = shape_parts(a)
    os.makedirs(OUT, exist_ok=True)
    sfx = "" if a.target == "lgf" else "_f"
    write_group(os.path.join(OUT, "shape_train%s.csv" % sfx), train, target=a.target)
    write_group(os.path.join(OUT, "shape_cal%s.csv" % sfx), cal, target=a.target)
    write_group(os.path.join(OUT, "shape_pts%s.csv" % sfx), pts, with_value=False, target=a.target)
    print("shape: train %d rows of %d cells; checked cells %d: calibration %d rows, continued %d rows" %
          (len(train), len(set(r["cell"] for r in train)), len(set(r["cell"] for r in cal)), len(cal), len(pts)))


def shape_run(a):
    cli = os.path.abspath(a.cli)
    tag = a.tag or "shape"
    forms = os.path.join(OUT, "nai_%s.forms" % tag)
    sfx = "" if a.target == "lgf" else "_f"
    out = subprocess.run([cli, "--data", os.path.join(OUT, "shape_train%s.csv" % sfx), "--seconds", str(a.seconds), "--seed", "1",
                          "--forms", forms] + a.nai.split(), capture_output=True, timeout=200 * a.seconds + 3600).stdout.decode("utf-8", "replace")
    open(os.path.join(OUT, "nai_%s.log" % tag), "w", encoding="utf-8").write(out)
    form = next((l.split("\t", 1)[1].strip() for l in open(forms, encoding="utf-8") if l.startswith("form\t")), "") if os.path.exists(forms) else ""
    best = [l for l in out.splitlines() if "ОДНА ФОРМА" in l or "ONE FORM" in l]
    print("%s: %s" % (tag, best[-1] if best else "no form"), flush=True)
    if not form:
        return
    fin = os.path.join(OUT, "nai_%s.form" % tag)
    open(fin, "w", encoding="utf-8").write(form + "\n")
    out2 = subprocess.run([cli, "--data", os.path.join(OUT, "shape_cal%s.csv" % sfx), "--seconds", "30", "--seed", "1",
                           "--candidates-in", fin, "--predict", os.path.join(OUT, "shape_pts%s.csv" % sfx),
                           os.path.join(OUT, "nai_%s.pred" % tag)], capture_output=True, timeout=7200).stdout.decode("utf-8", "replace")
    open(os.path.join(OUT, "nai_%s.cal.log" % tag), "w", encoding="utf-8").write(out2)
    json.dump({"nai": a.nai, "seconds": a.seconds, "form": form, "target": a.target}, open(os.path.join(OUT, "nai_%s.shape" % tag), "w", encoding="utf-8"))


def fit_cell(rs, kind):
    """A per-cell baseline fitted on a cell's first sweeps: a function x → lg f."""
    lx = [math.log10(r["x"] - 1 + 0.05) for r in rs]
    ly = [math.log10(r["f"]) for r in rs]
    if kind == "power":                         # lg f = a + b lg(x − 1 + 0.05)
        c = lsq([[1, v] for v in lx], ly)
        return lambda x, c=c: c[0] + c[1] * math.log10(x - 1 + 0.05)
    if kind == "linear":                        # f = a + b x
        c = lsq([[1, r["x"]] for r in rs], [r["f"] for r in rs])
        return lambda x, c=c: math.log10(max(c[0] + c[1] * x, 0.5))
    if kind == "sqrt":                          # f = a √(x − 1) + b
        c = lsq([[1, math.sqrt(r["x"] - 1)] for r in rs], [r["f"] for r in rs])
        return lambda x, c=c: math.log10(max(c[0] + c[1] * math.sqrt(x - 1), 0.5))
    if kind == "ln":                            # f = a + b ln x (the log form with two numbers, by least squares)
        c = lsq([[1, math.log(r["x"])] for r in rs], [r["f"] for r in rs])
        return lambda x, c=c: math.log10(max(c[0] + c[1] * math.log(x), 0.5))
    if kind in ("power3", "expsat", "lnc"):
        # three numbers: a + b·g(x; p), p on a grid, a and b by least squares, the best p by the squared error
        grids = {"power3": [k / 20 for k in range(2, 41)],              # g = (x − 1)^p
                 "expsat": [k / 4 for k in range(1, 81)],               # g = −exp(−x/p)
                 "lnc": [k / 40 for k in range(0, 39)]}                 # g = ln(x − p), p < 1
        g = {"power3": lambda x, p: (x - 1) ** p, "expsat": lambda x, p: -math.exp(-x / p),
             "lnc": lambda x, p: math.log(x - p)}[kind]
        best = None
        for p in grids[kind]:
            try:
                c = lsq([[1, g(r["x"], p)] for r in rs], [r["f"] for r in rs])
            except ZeroDivisionError:
                continue
            e = sum((c[0] + c[1] * g(r["x"], p) - r["f"]) ** 2 for r in rs)
            if best is None or e < best[0]:
                best = (e, p, c)
        _, p, c = best
        return lambda x, c=c, p=p: math.log10(max(c[0] + c[1] * g(x, p), 0.5))
    if kind == "log-quad":                      # lg f = a + b lg x + c (lg x)²
        c = lsq([[1, math.log10(r["x"]), math.log10(r["x"]) ** 2] for r in rs], ly)
        return lambda x, c=c: c[0] + c[1] * math.log10(x) + c[2] * math.log10(x) ** 2
    raise ValueError(kind)


def shape_score(a):
    train, cal, pts = shape_parts(a)
    calc = collections.defaultdict(list)
    for r in cal:
        calc[r["cell"]].append(r)
    preds = {}
    for kind in ("power", "linear", "sqrt", "ln", "lnc", "power3", "expsat"):
        fs = {c: fit_cell(rs, kind) for c, rs in calc.items()}
        preds["per cell: " + kind] = [fs[r["cell"]](r["x"]) for r in pts]
    for mf in sorted(glob.glob(os.path.join(OUT, "nai_*.shape"))):
        tag = os.path.basename(mf)[4:-6]
        pf = os.path.join(OUT, "nai_%s.pred" % tag)
        meta = json.load(open(mf, encoding="utf-8"))
        v = [float(l) for l in open(pf) if l.strip()] if os.path.exists(pf) else []
        if meta.get("target", "lgf") == "f":
            v = [math.log10(max(x, 0.5)) if math.isfinite(x) else float("nan") for x in v]
        preds["NAI " + tag] = v if len(v) == len(pts) else [None] * len(pts)
        print("NAI %s form: %s" % (tag, meta["form"]))
    print("continued on %d rows of %d cells (their upper 40 %% of currents, from the lower 60 %%); |log10(f_pred/f)|" %
          (len(pts), len(set(r["cell"] for r in pts))))
    print("%-24s %8s %8s %8s" % ("", "mean", "median", "90th pct"))
    for k, v in preds.items():
        e = sorted(abs(p - math.log10(r["f"])) if p is not None and math.isfinite(p) else 3.0 for p, r in zip(v, pts))
        print("%-24s %8.4f %8.4f %8.4f" % (k, statistics.mean(e), statistics.median(e), e[int(0.9 * len(e))]))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "split", "run", "score", "shape-split", "shape-run", "shape-score"])
    ap.add_argument("--out", default=DATA)
    ap.add_argument("--cli", default=os.path.join(HERE, "results", "v21", "nai_cli_v21.exe"))
    ap.add_argument("--seconds", type=float, default=300)
    ap.add_argument("--explore", action="store_true")
    ap.add_argument("--cut", type=int, default=1)
    ap.add_argument("--table", default="x", choices=list(TABLES))
    ap.add_argument("--tag", default="")
    ap.add_argument("--nai", default="")
    ap.add_argument("--cells", type=int, default=60, help="shape: cells in the table NAI searches")
    ap.add_argument("--target", default="lgf", choices=["lgf", "f"], help="shape: log10 f or f itself")
    a = ap.parse_args()
    global OUT
    if a.explore:
        OUT = os.path.join(OUT, "explore", "cut%d" % a.cut)
    {"fetch": fetch, "split": split, "run": run, "score": score, "shape-split": shape_split,
     "shape-run": shape_run, "shape-score": shape_score}[a.cmd](a)


if __name__ == "__main__":
    main()
