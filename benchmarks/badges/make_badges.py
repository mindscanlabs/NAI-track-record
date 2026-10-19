"""Place badges for the README: the place in a laurel wreath, the benchmark above,
the result below. One SVG per badge; GitHub's light and dark themes inside it
(prefers-color-scheme). Colors as in ../charts/make_charts.py.

    python benchmarks/badges/make_badges.py
"""
import math
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

# (file, place, caption, result)
BADGES = [
    ("sldbench", "1", "SLDBench · scaling laws", "Mean R² 0.775"),
    ("feynman", "1", "SRBench 2021 · Feynman", "60.3 % recovered exactly"),
    ("feynman_noise", "1", "SRBench 2021 · Feynman, 1 % noise", "48.3 % recovered exactly"),
    ("strogatz", "1", "SRBench 2021 · ODE-Strogatz", "85.7 % recovered exactly"),
    ("first_principles", "1", "SRBench 2025 · real data", "Median R² 0.9925, of 28"),
    ("llmsrbench", "1", "LLM-SRBench · new equations", "Chemistry, biology, physics"),
]

H = 54
CX, CY, R = 30, 27, 17          # the wreath


def width(text, size, bold=False, caps=False, spacing=0.0):
    """An estimate of the rendered width, a little generous (no font metrics here)."""
    per = 0.56 if caps else (0.53 if bold else 0.5)
    return len(text) * (size * per + spacing)


def wreath():
    """Two branches of leaves rising from the bottom along both sides, open at the top."""
    out = []
    for side in (1, -1):
        pt = lambda t: (CX + side * R * math.sin(math.radians(t)), CY + R * math.cos(math.radians(t)))
        # the stem, from near the bottom to near the top
        (x0, y0), (x1, y1) = pt(8), pt(136)
        out.append('<path class="stem" d="M%.2f %.2f A%d %d 0 0 %d %.2f %.2f"/>' % (x0, y0, R, R, 0 if side > 0 else 1, x1, y1))
        # Leaves grow the way the branch grows, up from the bottom: each one's base
        # on the stem, its tip forward along the stem and turned outwards; the
        # last one ends the branch. Smaller towards the top.
        for k in range(9):
            t = 18 + k * 15
            x, y = pt(t)
            r = math.radians(t)
            fwd = (side * math.cos(r), -math.sin(r))          # along the stem, the way it grows
            out_ = (side * math.sin(r), math.cos(r))          # away from the centre
            turn = math.radians(10 if k == 8 else 36)
            ax = (math.cos(turn) * fwd[0] + math.sin(turn) * out_[0], math.cos(turn) * fwd[1] + math.sin(turn) * out_[1])
            size = 1.0 - 0.045 * k
            L, w = 9.0 * size, 3.6 * size
            # in the badge's own coordinates, no transform: the gradient then
            # runs over the whole wreath, not over each leaf turned its own way
            nx, ny = -ax[1], ax[0]
            mx, my = x + ax[0] * L / 2, y + ax[1] * L / 2
            out.append('<path class="leaf" d="M%.2f %.2f Q%.2f %.2f %.2f %.2f Q%.2f %.2f %.2f %.2fZ"/>'
                       % (x, y, mx + nx * w, my + ny * w, x + ax[0] * L, y + ax[1] * L, mx - nx * w, my - ny * w, x, y))
    return "\n".join(out)


def ordinal(place):
    n = int(place)
    return place + ("th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def svg(place, caption, result):
    cap = caption.upper()
    said = "%s place, %s: %s" % (ordinal(place), caption, result)
    w = int(66 + max(width(cap, 9.5, caps=True, spacing=0.6), width(result, 14, bold=True)) + 14)
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">'
        % (w, H, w, H, escape(said)),
        '<title>%s</title>' % escape(said),
        # gold, lighter at the top of the wreath and deeper at its base
        '<defs>',
        '  <linearGradient id="gold" gradientUnits="userSpaceOnUse" x1="0" y1="%d" x2="0" y2="%d">' % (CY - R - 4, CY + R + 4),
        '    <stop offset="0" stop-color="#ecc54a"/><stop offset="0.55" stop-color="#d29a1c"/><stop offset="1" stop-color="#9c6a0e"/>',
        '  </linearGradient>',
        '  <linearGradient id="gold-dark" gradientUnits="userSpaceOnUse" x1="0" y1="%d" x2="0" y2="%d">' % (CY - R - 4, CY + R + 4),
        '    <stop offset="0" stop-color="#ffe08a"/><stop offset="0.55" stop-color="#e8b53a"/><stop offset="1" stop-color="#c08a1e"/>',
        '  </linearGradient>',
        '</defs>',
        '<style>',
        '  .bg { fill: #ffffff; stroke: #d0d7de; } .leaf { fill: url(#gold); } .stem { fill: none; stroke: url(#gold); stroke-width: 1.1; }',
        '  .place { fill: #0b0b0b; } .cap { fill: #2a78d6; } .res { fill: #0b0b0b; }',
        '  @media (prefers-color-scheme: dark) {',
        '    .bg { fill: #161b22; stroke: #30363d; } .leaf { fill: url(#gold-dark); } .stem { stroke: url(#gold-dark); }',
        '    .place { fill: #f0efec; } .cap { fill: #3987e5; } .res { fill: #f0efec; }',
        '  }',
        '</style>',
        '<rect class="bg" x="0.5" y="0.5" width="%d" height="%d" rx="8"/>' % (w - 1, H - 1),
        wreath(),
        '<text class="place" x="%d" y="%d" text-anchor="middle" font-family="%s" font-size="19" font-weight="700">%s</text>'
        % (CX, CY + 7, FONT, escape(place)),
        '<text class="cap" x="66" y="22" font-family="%s" font-size="9.5" font-weight="600" letter-spacing="0.6">%s</text>'
        % (FONT, escape(cap)),
        '<text class="res" x="66" y="40" font-family="%s" font-size="14" font-weight="700">%s</text>' % (FONT, escape(result)),
        '</svg>',
    ]) + "\n"


def main():
    for name, place, caption, result in BADGES:
        with open(os.path.join(HERE, name + ".svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg(place, caption, result))
        print(name)


if __name__ == "__main__":
    main()
