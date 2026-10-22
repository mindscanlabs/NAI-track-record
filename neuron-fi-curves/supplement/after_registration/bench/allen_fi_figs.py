"""
The figures of the f–I note (docs/ALLEN_FI.md), as SVG with the standard library only; then PDF through
Edge's headless printing. Test cells: the registered test's cells (the figures show, they test nothing).

    python bench/allen_fi_figs.py [--out D:/Claude/papers/allen_fi/figs]
"""
import argparse, importlib.util, json, math, os, re, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("p", os.path.join(HERE, "allen_fi_paper.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
INK, MUTED, GRID = "#1a1a1a", "#666666", "#dddddd"
FS_TICK, FS_LAB = 14, 15          # the same in every figure: the page prints all of them at one scale
COL = {"data": "#1a1a1a", "kln": "#c0392b", "line": "#2471a3", "glif": "#7d8c2a"}


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, s, size=11, anchor="start", color=INK, weight="normal", rotate=None):
        tr = ' transform="rotate(%g %g %g)"' % (rotate, x, y) if rotate else ""
        self.add('<text x="%.1f" y="%.1f" font-size="%g" text-anchor="%s" fill="%s" font-weight="%s"%s>%s</text>'
                 % (x, y, size, anchor, color, weight, tr, subscripts(s, size)))

    def line(self, x1, y1, x2, y2, color=INK, width=1, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%g"%s/>' % (x1, y1, x2, y2, color, width, d))

    def poly(self, pts, color, width=1.6, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<polyline fill="none" stroke="%s" stroke-width="%g"%s points="%s"/>' % (color, width, d, " ".join("%.1f,%.1f" % q for q in pts)))

    def dot(self, x, y, r=3, color=INK, fill=None, width=1.2):
        self.add('<circle cx="%.1f" cy="%.1f" r="%g" fill="%s" stroke="%s" stroke-width="%g"/>' % (x, y, r, fill or color, color, width))

    def rect(self, x, y, w, h, color):
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, y, w, h, color))

    def save(self, path):
        open(path, "w", encoding="utf-8").write(
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica, Arial, sans-serif">'
            '<rect width="100%%" height="100%%" fill="white"/>%s</svg>' % (self.w, self.h, self.w, self.h, "".join(self.items)))


def subscripts(s, size):
    """'I_rh', 'tau_m' and 'log10' with the subscript lowered and smaller; a zero-width tspan takes the baseline back."""
    d, small = 0.3 * size, 0.72 * size
    def one(m):
        base, sub = ("log", "10") if m.group(0) == "log10" else (m.group(1), m.group(2))
        return '%s<tspan dy="%.1f" font-size="%.1f">%s</tspan><tspan dy="%.1f">​</tspan>' % (base, d, small, sub, -d)
    return re.sub(r"log10|(\S)_(rh|m)", one, s)


def nice_ticks(lo, hi, n=5):
    """Round ticks inside [lo, hi]: a step of 1, 2, 2.5 or 5 times a power of ten."""
    raw = (hi - lo) / max(1, n)
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10)), key=lambda st: abs(st - raw))
    t = math.ceil(lo / step - 1e-9) * step
    out = []
    while t <= hi + 1e-9:
        out.append(round(t, 10))
        t += step
    return out


def panel(svg, x0, y0, w, h, xr, yr, xt, yt, xlabel, ylabel, title=None):
    sx = lambda x: x0 + (x - xr[0]) / (xr[1] - xr[0]) * w
    sy = lambda y: y0 + h - (y - yr[0]) / (yr[1] - yr[0]) * h
    xt = nice_ticks(*xr, 4) if xt is None else [t for t in xt if xr[0] - 1e-9 <= t <= xr[1] + 1e-9]
    yt = nice_ticks(*yr, 4) if yt is None else [t for t in yt if yr[0] - 1e-9 <= t <= yr[1] + 1e-9]
    for t in yt:
        svg.line(x0, sy(t), x0 + w, sy(t), GRID, 0.6)
        svg.text(x0 - 7, sy(t) + 5, "%g" % t, FS_TICK, "end", MUTED)
    for t in xt:
        svg.text(sx(t), y0 + h + 18, "%g" % t, FS_TICK, "middle", MUTED)
    svg.line(x0, y0 + h, x0 + w, y0 + h, INK, 0.8)
    svg.line(x0, y0, x0, y0 + h, INK, 0.8)
    svg.text(x0 + w / 2, y0 + h + 39, xlabel, FS_LAB, "middle")
    svg.text(x0 - 42, y0 + h / 2, ylabel, FS_LAB, "middle", rotate=-90)
    if title:
        svg.text(x0, y0 - 9, title, FS_LAB, "start", INK, "bold")
    return sx, sy


def fig_curves(out, sets, cells):
    """Six test cells: the rates, k·ln x from the rheobase and the sweep nearest x = 2, the line through the
    threshold and that sweep, and the cell's own GLIF3 model."""
    cc = sets["test"]
    ok = [cid for cid, rs in sorted(cc.items()) if os.path.exists(os.path.join(p.GDIR, "%d_glif3.json" % cid)) and len(rs) >= 8]
    pick, seen = [], set()
    for want in (("mouse", "spiny"), ("mouse", "aspiny"), ("human", "spiny"), ("mouse", "spiny"), ("mouse", "aspiny"), ("human", "spiny")):
        for cid in ok:
            c = cells[cid]
            sp = "human" if c["donor__species"] == "Homo Sapiens" else "mouse"
            if cid not in seen and (sp, c["tag__dendrite_type"]) == want:
                pick.append(cid); seen.add(cid); break
    svg = Svg(780, 830)
    for i, cid in enumerate(pick):
        rs = cc[cid]
        cfg = json.load(open(os.path.join(p.GDIR, "%d_glif3.json" % cid)))
        xs = [1 + j * (max(r["x"] for r in rs) - 1) / 60 for j in range(61)]
        ith = rs[0]["I"] / rs[0]["x"]
        glif = p.glif_rates([cfg] * len(xs), [x * ith for x in xs])
        r1 = min([r for r in rs if r["x"] > 1.2], key=lambda r: abs(r["x"] - 2))
        k = r1["f"] / math.log(r1["x"])
        ymax = max(max(r["f"] for r in rs), max(glif)) * 1.1
        col, row = i % 2, i // 2
        c = cells[cid]
        title = "%s, %s (I_rh %d pA)" % ("human" if c["donor__species"] == "Homo Sapiens" else "mouse", c["tag__dendrite_type"], round(ith))
        sx, sy = panel(svg, 75 + col * 395, 30 + row * 252, 295, 170, (1, xs[-1]), (0, ymax), None, None,
                       "I / I_rh", "rate (Hz)", title)
        svg.poly([(sx(x), sy(g)) for x, g in zip(xs, glif)], COL["glif"], 1.4, "4,3")
        svg.poly([(sx(x), sy(r1["f"] * (x - 1) / (r1["x"] - 1))) for x in xs if r1["f"] * (x - 1) / (r1["x"] - 1) <= ymax], COL["line"], 1.4)
        svg.poly([(sx(x), sy(k * math.log(x))) for x in xs if k * math.log(x) <= ymax], COL["kln"], 1.8)
        for r in rs:
            svg.dot(sx(r["x"]), sy(r["f"]), 3.4, COL["data"], "white" if r is r1 else None)
        svg.dot(sx(r1["x"]), sy(r1["f"]), 5.5, COL["kln"], "none", 1.8)
    for j, (lab, color, dash) in enumerate( (("data (open: the calibration step)", COL["data"], None), ("k·ln(I/I_rh), k from that step", COL["kln"], None),
                             ("line through threshold and that step", COL["line"], None), ("the cell's own GLIF3 model", COL["glif"], "4,3"))):
        lx, ly = 75 + (j % 2) * 395, 790 + (j // 2) * 24
        if lab.startswith("data"):
            svg.dot(lx + 10, ly - 5, 3.4, color)
        else:
            svg.line(lx, ly - 5, lx + 20, ly - 5, color, 2, dash)
        svg.text(lx + 26, ly, lab, FS_LAB)
    svg.save(os.path.join(out, "fig1_curves.svg"))


def fig_errors(out):
    """Mean and median error on the test cells with GLIF models (paper/glif_test.json)."""
    d = json.load(open(os.path.join(p.OUT, "glif_test.json")))
    order = [("GLIF1 (the cell's own model)", "GLIF1"), ("GLIF3 (the cell's own model)", "GLIF3"),
             ("line through threshold + one sweep", "line, one step"), ("k ln x, rheobase + one sweep", "k·ln x, one step")]
    svg = Svg(640, 320)
    sx, sy = panel(svg, 80, 30, 530, 240, (0, 4), (0, 0.6), [], [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], "", "|log10(predicted / measured)|")
    for i, (key, lab) in enumerate(order):
        mean, med, n = d[key]
        x = sx(i + 0.5)
        color = COL["kln"] if "k ln" in key else COL["line"] if "line" in key else COL["glif"]
        svg.rect(x - 44, sy(mean), 40, sy(0) - sy(mean), color)
        svg.rect(x + 4, sy(med), 40, sy(0) - sy(med), color + "88")
        svg.text(x - 24, sy(mean) - 5, "%.2f" % mean, FS_TICK, "middle", MUTED)
        svg.text(x + 24, sy(med) - 5, "%.2f" % med, FS_TICK, "middle", MUTED)
        svg.text(x, sy(0) + 22, lab, FS_LAB, "middle")
    for j, (lab, shade) in enumerate((("mean", "#666666"), ("median", "#66666688"))):     # the key: dark and light bars
        svg.rect(470, 42 + j * 24, 18, 13, shade)
        svg.text(496, 54 + j * 24, lab, FS_LAB)
    svg.save(os.path.join(out, "fig2_errors.svg"))


def fig_tau(out, sets, cells):
    """lg k against lg tau, all cells with ≥ 7 points (working and test), by dendrite type; slope −1 drawn."""
    svg = Svg(560, 365)
    pts = []
    for name, cc in sets.items():
        for cid, rs in cc.items():
            lx = [math.log(r["x"]) for r in rs]
            k = sum(l * r["f"] for l, r in zip(lx, rs)) / max(1e-12, sum(l * l for l in lx))
            if k > 0:
                pts.append((math.log10(rs[0]["tau"]), math.log10(k), cells[cid]["tag__dendrite_type"]))
    sx, sy = panel(svg, 125, 20, 360, 260, (0.4, 1.8), (0, 3), [0.5, 1, 1.5], [0, 1, 2, 3], "log10 τ_m (ms)", "log10 k (Hz)")
    for x, y, t in pts:
        if 0.4 <= x <= 1.8 and 0 <= y <= 3:
            svg.dot(sx(x), sy(y), 1.6, "#c0392b" if t == "aspiny" else "#2471a3", None, 0.4)
    for t, color in (("aspiny", "#c0392b"), ("spiny", "#2471a3")):
        sub = [(x, y) for x, y, tt in pts if (tt == "aspiny") == (t == "aspiny")]
        b = statistics.median(y + x for x, y in sub)          # the line of slope −1 through the median of lg k + lg tau
        svg.line(sx(0.45), sy(b - 0.45), sx(1.75), sy(b - 1.75), color, 1.6)
    svg.dot(20, 350, 4, "#2471a3")                                   # the key, below the axis label
    svg.text(30, 355, "spiny, sparsely spiny", FS_LAB)
    svg.dot(205, 350, 4, "#c0392b")
    svg.text(215, 355, "aspiny", FS_LAB)
    svg.line(285, 350, 305, 350, MUTED, 1.6)
    svg.text(312, 355, "slope −1 through the group median", FS_LAB)
    svg.save(os.path.join(out, "fig3_tau.svg"))


def to_pdf(out):
    for f in sorted(os.listdir(out)):
        if not f.endswith(".svg"):
            continue
        src = os.path.join(out, f)
        txt = open(src, encoding="utf-8").read()
        w = int(txt.split('width="')[1].split('"')[0]); h = int(txt.split('height="')[1].split('"')[0])
        html = os.path.join(out, f[:-4] + ".html")
        open(html, "w", encoding="utf-8").write('<!doctype html><html><head><style>@page{size:%dpx %dpx;margin:0}html,body{margin:0}</style></head><body>%s</body></html>' % (w, h, txt))
        pdf = os.path.join(out, f[:-4] + ".pdf")
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=" + os.path.join(out, ".edge"),
                        "--no-pdf-header-footer", "--print-to-pdf=" + os.path.abspath(pdf), "file:///" + os.path.abspath(html).replace("\\", "/")],
                       capture_output=True, timeout=120)
        os.remove(html)
        print(f, "->", os.path.basename(pdf), os.path.exists(pdf))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/Claude/papers/allen_fi/figs")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sets, cells = p.parts()
    fig_curves(a.out, sets, cells)
    fig_errors(a.out)
    fig_tau(a.out, sets, cells)
    to_pdf(a.out)


if __name__ == "__main__":
    main()
