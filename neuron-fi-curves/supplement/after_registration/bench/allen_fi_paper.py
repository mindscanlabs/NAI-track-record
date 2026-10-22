"""
f–I curves, the analyses for the preprint beyond the registration (docs/ALLEN_FI.md).
Each is printed for the working part and for the test cells separately; the test's numbers are a second
look at it, outside the registration.

    python bench/allen_fi_paper.py boxcox      the exponent d of f = k·(x^d − 1)/d per cell (d → 0: k ln x; d = 1: a line)
    python bench/allen_fi_paper.py groups      the registered checks A and B by species, dendrite type and layer (groups of ≥ 20 cells)
    python bench/allen_fi_paper.py glif-fetch  the Allen Institute's GLIF1 (LIF) and GLIF3 (LIF + after-spike currents)
                                               models of each cell → D:/Claude/nai-data/allen_ct/glif/
    python bench/allen_fi_paper.py glif        each model run on the cell's own Long Square currents (1 s), against the
                                               cell's rates, with the log law's predictions on the same rows
"""
import time, urllib.parse, urllib.request
import argparse, collections, importlib.util, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("af", os.path.join(HERE, "allen_fi.py"))
af = importlib.util.module_from_spec(spec)
spec.loader.exec_module(af)
OUT = os.path.join(af.OUT, "paper")


def parts():
    class A:
        pass
    a = A()
    a.out, a.explore, a.cut = af.DATA, False, 1
    work, test = af.load(a)                      # the working part, the test cells
    cells = {c["specimen__id"]: c for c in json.load(open(os.path.join(af.DATA, "cells.json"), encoding="utf-8"))}
    return {"working": af.cell_rows(work), "test": af.cell_rows(test)}, cells


def chi2_at(rs, d):
    """k·(x^d − 1)/d (k·ln x at d = 0) with k by weighted least squares through the origin; the counts'
    noise σ² = max(n, 1) (n spikes in the 1 s pulse). Returns (χ², k)."""
    g = (lambda x: math.log(x)) if abs(d) < 1e-9 else (lambda x: (x ** d - 1) / d)
    u = [g(r["x"]) for r in rs]
    w = [1.0 / max(r["f"], 1.0) for r in rs]
    den = sum(wi * v * v for wi, v in zip(w, u))
    if den <= 0:
        return float("inf"), 0.0
    k = sum(wi * v * r["f"] for wi, v, r in zip(w, u, rs)) / den
    return sum(wi * (k * v - r["f"]) ** 2 for wi, v, r in zip(w, u, rs)), k


def boxcox_fit(rs):
    """d on a grid from −4 to 4 (step 0.05): the d of least χ², and χ² at d = 0 (the log) and d = 1 (the line)."""
    best = min((chi2_at(rs, i / 20)[0], i / 20) for i in range(-80, 81))
    return best[1], best[0], chi2_at(rs, 0.0)[0], chi2_at(rs, 1.0)[0]


def corr(u, v):
    mu, mv = statistics.mean(u), statistics.mean(v)
    num = sum((p - mu) * (q - mv) for p, q in zip(u, v))
    return num / math.sqrt(sum((p - mu) ** 2 for p in u) * sum((q - mv) ** 2 for q in v))


def boxcox(a):
    sets, cells = parts()
    res = {}
    for name, cc in sets.items():
        ds, adapt = [], []
        ok_log = ok_lin = 0
        for cid, rs in cc.items():
            d, cbest, clog, clin = boxcox_fit(rs)
            ok_log += clog - cbest <= 4
            ok_lin += clin - cbest <= 4
            ds.append(d)
            ad = cells[cid]["ef__adaptation"]
            adapt.append((d, ad, cells[cid]["tag__dendrite_type"]))
        ds.sort()
        q = lambda p: ds[int(p * (len(ds) - 1))]
        hist = collections.Counter(max(-2.0, min(2.0, round(d * 2) / 2)) for d in ds)
        both = [(d, ad) for d, ad, _ in adapt if ad is not None and math.isfinite(ad)]
        res[name] = dict(cells=len(ds), median=q(0.5), q25=q(0.25), q75=q(0.75),
                         share_near0=sum(1 for d in ds if abs(d) <= 0.25) / len(ds),
                         share_near1=sum(1 for d in ds if abs(d - 1) <= 0.25) / len(ds),
                         compatible_log=ok_log / len(ds), compatible_line=ok_lin / len(ds),
                         at_edges=sum(1 for d in ds if abs(d) >= 3.95) / len(ds),
                         corr_d_adaptation=corr([d for d, _ in both], [ad for _, ad in both]) if len(both) > 3 else None,
                         by_type={t: statistics.median([d for d, _, tt in adapt if tt == t]) for t in set(t for _, _, t in adapt)},
                         hist=sorted(hist.items()))
        r = res[name]
        print("%s: %d cells; d median %.3f (quartiles %.3f to %.3f); |d| <= 0.25: %.0f %%, |d - 1| <= 0.25: %.0f %%; corr(d, adaptation index) %.3f"
              % (name, r["cells"], r["median"], r["q25"], r["q75"], 100 * r["share_near0"], 100 * r["share_near1"], r["corr_d_adaptation"]))
        print("   median d by dendrite type:", {k: round(v, 3) for k, v in r["by_type"].items()})
        print("   compatible within Δχ² ≤ 4 of the best d (count noise): the log %.0f %% of cells, the line through the threshold %.0f %%; d at the grid's edge (|d| = 4): %.0f %%"
              % (100 * r["compatible_log"], 100 * r["compatible_line"], 100 * r["at_edges"]))
        print("   histogram (d rounded to 0.5, the ends gather |d| >= 2):", " ".join("%g:%d" % kv for kv in r["hist"]))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "boxcox.json"), "w"), indent=1)


def groups(a):
    """Medians of checks A (a + b·ln x against a + b·x) and B (k·ln x against the line through the threshold) by
    species, dendrite type and layer; groups of fewer than 20 cells are left out."""
    spec2 = importlib.util.spec_from_file_location("ff", os.path.join(HERE, "allen_fi_final.py"))
    ff = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(ff)
    sets, cells = parts()
    e = lambda pv, f: abs(math.log10(max(pv, 0.5) / f))
    out = {}
    for name, cc in sets.items():
        grp = collections.defaultdict(lambda: collections.defaultdict(list))
        for cid, rs in cc.items():
            c = cells[cid]
            keys = ["all", "species: " + ("human" if c["donor__species"] == "Homo Sapiens" else "mouse"),
                    "dendrite: " + str(c["tag__dendrite_type"]), "layer: " + str(c["structure__layer"])]
            cand = [r for r in rs if r["x"] > 1.2]
            r1 = min(cand, key=lambda r: abs(r["x"] - 2)) if cand else None
            k = max(3, int(round(0.6 * len(rs))))
            fl, fn = ff.per_cell(rs[:k], "linear"), ff.per_cell(rs[:k], "ln")
            for key in keys:
                grp[key]["cells"].append(1)
                for r in rs[k:]:
                    grp[key]["A line"].append(e(fl(r["x"]), r["f"]))
                    grp[key]["A ln"].append(e(fn(r["x"]), r["f"]))
                if r1:
                    kk = r1["f"] / math.log(r1["x"])
                    for r in rs:
                        if r is not r1:
                            grp[key]["B kln"].append(e(kk * math.log(r["x"]), r["f"]))
                            grp[key]["B line"].append(e(r1["f"] * (r["x"] - 1) / (r1["x"] - 1), r["f"]))
        print("%s: medians, A a + b ln x against a + b x (continuation), B k ln x against the line (one step)" % name)
        for key in sorted(grp, key=lambda k: (k != "all", k)):
            g = grp[key]
            if len(g["cells"]) < 20:
                continue
            m = {k2: statistics.median(v) for k2, v in g.items() if k2 != "cells"}
            print("   %-26s %4d cells   A %.3f vs %.3f   B %.3f vs %.3f" % (key, len(g["cells"]), m["A ln"], m["A line"], m["B kln"], m["B line"]))
            out.setdefault(name, {})[key] = dict(cells=len(g["cells"]), **m)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "groups.json"), "w"), indent=1)


GLIF = {1: "1 Leaky Integrate and Fire (LIF)", 3: "3 LIF + Afterspike Currents (LIF-ASC)"}
GDIR = os.path.join(af.DATA, "glif")


def glif_fetch(a):
    os.makedirs(GDIR, exist_ok=True)
    for level, name in GLIF.items():
        models = af.rma("model::NeuronalModel,rma::criteria,neuronal_model_template[name$eq'%s'],rma::include,well_known_files" % name, page=500)
        got = 0
        for m in models:
            path = os.path.join(GDIR, "%d_glif%d.json" % (m["specimen_id"], level))
            wk = [w for w in m.get("well_known_files", []) if w["path"].endswith("neuron_config.json")]
            if os.path.exists(path) or not wk:
                continue
            url = "https://api.brain-map.org/api/v2/well_known_file_download/%d" % wk[0]["id"]
            for attempt in range(5):
                try:
                    open(path, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nai-bench/1.0"}), timeout=120).read())
                    got += 1
                    break
                except Exception as e:
                    if attempt == 4:
                        print("  failed:", m["specimen_id"], e)
                    time.sleep(3 * (attempt + 1))
        print("GLIF%d: %d models, %d downloaded" % (level, len(models), got), flush=True)


def glif_rates(cfgs, amps_pA, seconds=1.0):
    """The GLIF neurons (Allen SDK's equations: linear forward Euler, exponential after-spike currents, reset to
    0 and 'sum' of the currents, the spike cut skipped) for the currents given, all at once (numpy).
    cfgs: one config per run, amps_pA: one current per run. Returns spikes per second."""
    import numpy as np
    n = len(cfgs)
    dt = np.array([c["dt"] for c in cfgs])
    C = np.array([c["C"] * c["coeffs"]["C"] for c in cfgs])
    G = np.array([c["coeffs"]["G"] / c["R_input"] for c in cfgs])
    th = np.array([c["th_inf"] * c["coeffs"]["th_inf"] for c in cfgs])
    cut = np.array([c["spike_cut_length"] for c in cfgs])
    na = max(len(c["asc_amp_array"]) for c in cfgs)
    amp = np.zeros((n, na)); tau = np.ones((n, na)); r = np.zeros((n, na))
    for i, c in enumerate(cfgs):
        if c["AScurrent_dynamics_method"]["name"] == "none":     # GLIF1: the file carries amplitudes it does not use
            continue
        k = len(c["asc_amp_array"])
        amp[i, :k] = np.array(c["asc_amp_array"]) * np.array(c["coeffs"].get("asc_amp_array", [1.0] * k))
        tau[i, :k] = c["asc_tau_array"]
        r[i, :k] = c["AScurrent_reset_method"]["params"].get("r", [1.0] * k)
    I = np.array(amps_pA) * 1e-12
    V = np.zeros(n); A = np.zeros((n, na)); hold = np.zeros(n, dtype=int); spikes = np.zeros(n)
    decay = np.exp(-dt[:, None] / tau)
    steps = int(round(seconds / dt.min()))
    for _ in range(steps):
        active = hold <= 0
        V = np.where(active, V + (I + A.sum(1) - G * V) * dt / C, V)
        A = A * decay
        fire = active & (V > th)
        spikes += fire
        V = np.where(fire, 0.0, V)
        A = np.where(fire[:, None], A * r + amp, A)
        hold = np.where(fire, cut, hold - 1)
    return spikes / seconds


def glif(a):
    import numpy as np
    sets, cells = parts()
    for name, cc in sets.items():
        runs, meta = [], []
        for cid, rs in cc.items():
            files = {lv: os.path.join(GDIR, "%d_glif%d.json" % (cid, lv)) for lv in GLIF}
            if not all(os.path.exists(f) for f in files.values()):
                continue
            cf = {lv: json.load(open(f)) for lv, f in files.items()}
            for lv in GLIF:
                for r in rs:
                    runs.append(cf[lv]); meta.append((cid, lv, r))
        rates = glif_rates(runs, [m[2]["I"] for m in meta]) if runs else []
        pred = collections.defaultdict(dict)
        for (cid, lv, r), f in zip(meta, rates):
            pred[(cid, lv)][r["x"]] = f
        cids = sorted(set(m[0] for m in meta))
        E = collections.defaultdict(list)
        for cid in cids:
            rs = cc[cid]
            cand = [r for r in rs if r["x"] > 1.2]
            r1 = min(cand, key=lambda r: abs(r["x"] - 2)) if cand else None
            k = r1["f"] / math.log(r1["x"]) if r1 else None
            for r in rs:
                if r is r1:
                    continue
                for lv in GLIF:
                    E["GLIF%d (the cell's own model)" % lv].append(abs(math.log10(max(pred[(cid, lv)][r["x"]], 0.5) / r["f"])))
                if k:
                    E["k ln x, rheobase + one sweep"].append(abs(math.log10(max(k * math.log(r["x"]), 0.5) / r["f"])))
                    E["line through threshold + one sweep"].append(abs(math.log10(max(r1["f"] * (r["x"] - 1) / (r1["x"] - 1), 0.5) / r["f"])))
        print("%s: %d cells with GLIF1 and GLIF3 models (rows other than the calibration sweep); |lg f_pred/f| mean / median" % (name, len(cids)))
        for k2, v in E.items():
            print("   %-38s %.4f / %.4f (%d rows)" % (k2, statistics.mean(v), statistics.median(v), len(v)))
        json.dump({k2: [statistics.mean(v), statistics.median(v), len(v)] for k2, v in E.items()},
                  open(os.path.join(OUT, "glif_%s.json" % name), "w"), indent=1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["boxcox", "groups", "glif-fetch", "glif"])
    a = ap.parse_args()
    {"boxcox": boxcox, "groups": groups, "glif-fetch": glif_fetch, "glif": glif}[a.cmd](a)


if __name__ == "__main__":
    main()
