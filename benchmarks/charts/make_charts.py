"""Ranked horizontal bar charts for the README: one per benchmark, first place on
top, NAI in blue and the other systems in gray, each value at the bar's tip.
Two SVGs per chart, for GitHub's light and dark themes (<picture> in README.md).
Colors checked with a palette validator against GitHub's surfaces (#ffffff,
#0d1117): blue vs gray CVD dE >= 16, normal-vision dE >= 18, contrast >= 3:1.

    python benchmarks/charts/make_charts.py
"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
THEMES = {
    "light": {"nai": "#2a78d6", "other": "#8f8d86", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781", "base": "#c3c2b7"},
    "dark": {"nai": "#3987e5", "other": "#6f6d68", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781", "base": "#383835"},
}
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

# (file, accessible title, value format, axis maximum, rows); a row is (system, value) or
# (system, value, rank text) when rows were skipped above it; None marks the skipped rows.
CHARTS = [
    ("sldbench", "SLDBench: mean R² over 8 scaling-law tasks", "{:.3f}", 1.0, [
        ("NAI", 0.775), ("SLDAgent (GPT-5)", 0.748), ("Goose (GPT-5)", 0.695), ("SLDAgent (o4-mini)", 0.657),
        ("SLDAgent (Gemini 3 Pro)", 0.636), ("SLDAgent (Claude Sonnet 4.5)", 0.590), ("Gemini CLI (Gemini 3 Pro)", 0.587),
        ("Codex (GPT-5)", 0.550), ("SLDAgent (Claude Haiku 4.5)", 0.519), ("Human-designed laws", 0.517),
        ("OpenHands (GPT-5)", 0.516), ("SLDAgent (Gemini 2.5 Flash)", 0.506), ("OpenCode (GPT-5)", 0.501)]),
    ("feynman", "SRBench 2021: Feynman equations recovered exactly, no noise (%)", "{:.1f}", 100.0, [
        ("NAI", 60.3), ("AI Feynman", 55.8), ("AFP_FE", 27.0), ("GP-GOMEA", 26.8), ("ITEA", 22.4), ("AFP", 21.1),
        ("DSR", 19.7), ("Operon", 16.6), ("gplearn", 16.3), ("SBP-GP", 12.7), ("EPLEX", 12.4), ("BSR", 2.5),
        ("FEAT", 0.0), ("FFX", 0.0), ("MRGP", 0.0)]),
    ("feynman_noise", "SRBench 2021: Feynman equations recovered exactly, 1 % noise (%)", "{:.1f}", 100.0, [
        ("NAI", 48.3), ("gplearn", 13.2), ("EPLEX", 8.8), ("DSR", 8.4), ("AFP", 7.1), ("AFP_FE", 6.1), ("ITEA", 0.1),
        ("Operon", 0.1), ("AI Feynman", 0.0), ("BSR", 0.0), ("FEAT", 0.0), ("FFX", 0.0), ("GP-GOMEA", 0.0),
        ("MRGP", 0.0), ("SBP-GP", 0.0)]),
    ("strogatz", "SRBench 2021: ODE-Strogatz systems recovered exactly (%)", "{:.1f}", 100.0, [
        ("NAI", 85.7), ("GP-GOMEA", 29.5), ("AI Feynman", 27.1), ("AFP_FE", 20.0), ("DSR", 19.6), ("AFP", 15.2),
        ("SBP-GP", 11.6), ("Operon", 11.4), ("EPLEX", 8.9), ("gplearn", 8.9), ("ITEA", 7.1), ("BSR", 0.9),
        ("FEAT", 0.9), ("FFX", 0.0), ("MRGP", 0.0)]),
    ("first_principles", "SRBench 2025: real measurements of physical laws, median R² (top 12 of 28)", "{:.3f}", 1.0, [
        ("NAI", 0.9925), ("QLattice", 0.9867), ("PySR", 0.9135), ("Operon", 0.9130), ("Rils-Rols", 0.9012),
        ("Bingo", 0.8941), ("GPZGD", 0.8868), ("EQL", 0.8750), ("FFX", 0.8721), ("AFP_FE", 0.8403), ("AFP", 0.8291),
        ("ITEA", 0.8244)]),
    ("black_box", "SRBench 2025: black-box regression, mean R² (top 8 of 29, and NAI)", "{:.3f}", 1.0, [
        ("Rils-Rols", 0.640), ("QLattice", 0.637), ("EQL", 0.634), ("Operon", 0.629), ("ITEA", 0.628), ("Brush", 0.627),
        ("PS-Tree", 0.620), ("FEAT", 0.609), None, ("NAI", 0.090, "26th")]),
    ("llmsr_transform", "LLM-SRBench: LSR-Transform, Acc0.1 (%)", "{:.2f}", 100.0, [('NAI', 72.07), ('LaSR (GPT-4o-mini)', 50.45), ('LaSR (GPT-3.5-turbo)', 47.74), ('LaSR (Llama-3.1-8B)', 45.94), ('LLM-SR (GPT-4o-mini)', 39.64), ('LLM-SR (Llama-3.1-8B)', 38.55), ('LLM-SR (GPT-3.5-turbo)', 10.81), ('SGA (GPT-4o-mini)', 8.11), ('Direct prompting (GPT-4o-mini)', 6.31), ('Direct prompting (Llama-3.1-8B)', 1.8), ('Direct prompting (GPT-3.5-turbo)', 1.8), ('SGA (Llama-3.1-8B)', 0.91), ('SGA (GPT-3.5-turbo)', 0.91)]),
    ("llmsr_chem", "LLM-SRBench: LSR-Synth chemistry, Acc0.1 (%)", "{:.2f}", 100.0, [('NAI', 91.67), ('LLM-SR (Llama-3.1-8B)', 66.66), ('LLM-SR (GPT-4o-mini)', 52.77), ('LLM-SR (GPT-3.5-turbo)', 50.22), ('LaSR (GPT-4o-mini)', 38.92), ('LaSR (GPT-3.5-turbo)', 38.89), ('LaSR (Llama-3.1-8B)', 27.77), ('SGA (GPT-4o-mini)', 16.66), ('Direct prompting (GPT-4o-mini)', 13.88), ('SGA (Llama-3.1-8B)', 8.33), ('SGA (GPT-3.5-turbo)', 8.33), ('Direct prompting (GPT-3.5-turbo)', 8.33), ('Direct prompting (Llama-3.1-8B)', 0.0)]),
    ("llmsr_bio", "LLM-SRBench: LSR-Synth biology, Acc0.1 (%)", "{:.2f}", 100.0, [('NAI', 70.83), ('LLM-SR (Llama-3.1-8B)', 58.33), ('LLM-SR (GPT-4o-mini)', 29.16), ('LLM-SR (GPT-3.5-turbo)', 25.03), ('LaSR (GPT-4o-mini)', 20.83), ('LaSR (Llama-3.1-8B)', 16.66), ('LaSR (GPT-3.5-turbo)', 16.66), ('SGA (GPT-4o-mini)', 12.51), ('SGA (GPT-3.5-turbo)', 8.33), ('Direct prompting (GPT-3.5-turbo)', 4.16), ('Direct prompting (GPT-4o-mini)', 4.16), ('SGA (Llama-3.1-8B)', 0.0), ('Direct prompting (Llama-3.1-8B)', 0.0)]),
    ("llmsr_phys", "LLM-SRBench: LSR-Synth physics, Acc0.1 (%)", "{:.2f}", 100.0, [('NAI', 47.73), ('LLM-SR (GPT-4o-mini)', 36.36), ('LLM-SR (Llama-3.1-8B)', 34.09), ('LaSR (GPT-4o-mini)', 31.81), ('LLM-SR (GPT-3.5-turbo)', 25.12), ('LaSR (Llama-3.1-8B)', 25.02), ('LaSR (GPT-3.5-turbo)', 22.71), ('Direct prompting (GPT-4o-mini)', 9.09), ('SGA (GPT-4o-mini)', 9.09), ('SGA (GPT-3.5-turbo)', 4.54), ('Direct prompting (GPT-3.5-turbo)', 2.27), ('SGA (Llama-3.1-8B)', 2.27), ('Direct prompting (Llama-3.1-8B)', 0.0)]),
    ("llmsr_matsci", "LLM-SRBench: LSR-Synth materials science, Acc0.1 (%)", "{:.2f}", 100.0, [('LLM-SR (GPT-4o-mini)', 88.28), ('LLM-SR (Llama-3.1-8B)', 88.12), ('NAI', 84.0), ('LLM-SR (GPT-3.5-turbo)', 82.14), ('LaSR (GPT-4o-mini)', 72.04), ('LaSR (Llama-3.1-8B)', 64.22), ('LaSR (GPT-3.5-turbo)', 64.09), ('SGA (GPT-4o-mini)', 36.11), ('SGA (GPT-3.5-turbo)', 28.1), ('SGA (Llama-3.1-8B)', 12.12), ('Direct prompting (Llama-3.1-8B)', 0.0), ('Direct prompting (GPT-3.5-turbo)', 0.0), ('Direct prompting (GPT-4o-mini)', 0.0)]),
]

ROW, BAR, W, LABEL_W, VALUE_W = 26, 16, 760, 250, 64


def svg(chart, theme):
    name, title, fmt, vmax, rows = chart
    t = THEMES[theme]
    x0 = LABEL_W + 10
    span = W - x0 - VALUE_W
    h = ROW * len(rows) + 8
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-labelledby="t d">'
           % (W, h, W, h),
           '<title id="t">%s</title>' % escape(title),
           '<desc id="d">%s</desc>' % escape("; ".join("%s %s" % (r[0], fmt.format(r[1])) for r in rows if r)),
           '<g font-family="%s" font-size="13">' % FONT]
    for i, r in enumerate(rows):
        cy = 4 + ROW * i + ROW / 2
        if r is None:
            out.append('<text x="%d" y="%.1f" fill="%s" text-anchor="end" dominant-baseline="central">⋯</text>' % (LABEL_W, cy, t["muted"]))
            continue
        who, v = r[0], r[1]
        nai = who == "NAI"
        label = who + (" (%s)" % r[2] if len(r) > 2 else "")
        out.append('<text x="%d" y="%.1f" fill="%s" text-anchor="end" dominant-baseline="central"%s>%s</text>'
                   % (LABEL_W, cy, t["ink"] if nai else t["ink2"], ' font-weight="700"' if nai else "", escape(label)))
        length = max(0.0, v) / vmax * span
        y = cy - BAR / 2
        if length >= 4:      # square at the baseline, 4 px round at the data end
            out.append('<path d="M%.1f %.1f H%.1f a4 4 0 0 1 4 4 V%.1f a4 4 0 0 1 -4 4 H%.1f Z" fill="%s"/>'
                       % (x0, y, x0 + length - 4, y + BAR - 4, x0, t["nai" if nai else "other"]))
        elif length > 0:
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%d" fill="%s"/>' % (x0, y, length, BAR, t["nai" if nai else "other"]))
        out.append('<text x="%.1f" y="%.1f" fill="%s" dominant-baseline="central"%s>%s</text>'
                   % (x0 + length + 6, cy, t["ink"] if nai else t["ink2"], ' font-weight="700"' if nai else "", fmt.format(v)))
    out.append('<line x1="%d" y1="2" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (x0, x0, h - 2, t["base"]))
    out.append('</g></svg>')
    return "\n".join(out) + "\n"


def main():
    for chart in CHARTS:
        for theme in THEMES:
            with open(os.path.join(HERE, "%s_%s.svg" % (chart[0], theme)), "w", encoding="utf-8", newline="\n") as f:
                f.write(svg(chart, theme))
    print("%d charts, %d files" % (len(CHARTS), 2 * len(CHARTS)))


if __name__ == "__main__":
    main()
