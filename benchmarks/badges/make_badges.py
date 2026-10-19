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
    ("sldbench", "#1", "SLDBench · scaling laws", "Mean R² 0.775"),
    ("feynman", "#1", "SRBench 2021 · Feynman", "60.3 % recovered exactly"),
    ("feynman_noise", "#1", "SRBench 2021 · Feynman, 1 % noise", "48.3 % recovered exactly"),
    ("strogatz", "#1", "SRBench 2021 · ODE-Strogatz", "85.7 % recovered exactly"),
    ("first_principles", "#1", "SRBench 2025 · real data", "Median R² 0.9925, of 28"),
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
        (x0, y0), (x1, y1) = pt(8), pt(142)
        out.append('<path class="stem" d="M%.2f %.2f A%d %d 0 0 %d %.2f %.2f"/>' % (x0, y0, R, R, 0 if side > 0 else 1, x1, y1))
        # Leaves grow the way the branch grows, up from the bottom: each one's base
        # on the stem, its tip forward along the stem and turned outwards; the
        # last one ends the branch. Smaller towards the top.
        for k in range(7):
            t = 22 + k * 20
            x, y = pt(t)
            r = math.radians(t)
            fwd = (side * math.cos(r), -math.sin(r))          # along the stem, the way it grows
            out_ = (side * math.sin(r), math.cos(r))          # away from the centre
            turn = math.radians(10 if k == 6 else 38)
            ax = (math.cos(turn) * fwd[0] + math.sin(turn) * out_[0], math.cos(turn) * fwd[1] + math.sin(turn) * out_[1])
            deg = math.degrees(math.atan2(ax[1], ax[0]))
            size = 1.0 - 0.06 * k
            L, w = 8.5 * size, 2.7 * size
            out.append('<path class="leaf" transform="translate(%.2f %.2f) rotate(%.1f)" d="M0 0 Q%.2f %.2f %.2f 0 Q%.2f %.2f 0 0Z"/>'
                       % (x, y, deg, L / 2, -w, L, L / 2, w))
    return "\n".join(out)


def svg(place, caption, result):
    cap = caption.upper()
    w = int(66 + max(width(cap, 9.5, caps=True, spacing=0.6), width(result, 14, bold=True)) + 14)
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">'
        % (w, H, w, H, escape("%s %s: %s" % (place, caption, result))),
        '<title>%s</title>' % escape("%s, %s: %s" % (place, caption, result)),
        '<style>',
        '  .bg { fill: #ffffff; stroke: #d0d7de; } .leaf { fill: #2a78d6; } .stem { fill: none; stroke: #2a78d6; stroke-width: 1; }',
        '  .place { fill: #0b0b0b; } .cap { fill: #2a78d6; } .res { fill: #0b0b0b; }',
        '  @media (prefers-color-scheme: dark) {',
        '    .bg { fill: #161b22; stroke: #30363d; } .leaf { fill: #3987e5; } .stem { stroke: #3987e5; }',
        '    .place { fill: #f0efec; } .cap { fill: #3987e5; } .res { fill: #f0efec; }',
        '  }',
        '</style>',
        '<rect class="bg" x="0.5" y="0.5" width="%d" height="%d" rx="8"/>' % (w - 1, H - 1),
        wreath(),
        '<text class="place" x="%d" y="%d" text-anchor="middle" font-family="%s" font-size="14" font-weight="700">%s</text>'
        % (CX, CY + 5, FONT, escape(place)),
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
