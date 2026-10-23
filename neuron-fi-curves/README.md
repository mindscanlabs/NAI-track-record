# The Whole f–I Curve of a Neuron from Its Rheobase and One Current Step

Mikhail Smirnov, preprint, October 2026. Zenodo, DOI [10.5281/zenodo.23582787](https://doi.org/10.5281/zenodo.23582787).
[PDF](neuron-fi-curves.pdf) · [LaTeX source](neuron-fi-curves.tex) · [registration, programs and results](supplement/)

Full title: *The whole f–I curve of a neuron from its rheobase and one current step: a
pre-registered test of a one-parameter logarithmic law on the Allen Cell Types Database.*

## Abstract

The frequency–current (f–I) curve of a neuron is usually summarised by the slope of a
straight line above the rheobase, or by a fitted neuron model. I tested a one-parameter
law, f = k·ln(I/I_rh), where I_rh is the rheobase, on 2,333 mouse and human neurons of the
Allen Cell Types Database (58,585 one-second current steps). The hypotheses, the data
split and the error measure were fixed and fingerprinted before a single look at 700
held-out cells. The error of a predicted rate is |log10(f_pred/f)|, in decades. On the 588
held-out cells with at least seven suprathreshold steps, calibrating k from the rheobase
and one step near 2·I_rh predicts the rest of the curve with a median error of 0.084
decades (a factor of 1.21), against 0.120 decades (1.32) for a straight line through the
same two points. Fitted to the lowest 60 % of a cell's steps, the two-parameter form
a + b·ln(I/I_rh) predicts the remaining, higher steps with a median error of 0.054
decades, against 0.074 for a straight line. The zero of the fitted logarithm lies at the
rheobase (median I_0/I_rh = 0.987). Outside the registration, on the 331 held-out cells
with published generalized leaky integrate-and-fire models (GLIF3), the cells' own models
predicted the rates with a median error of 0.200 decades, against 0.078 for the one-step
law, and k scaled close to 1/τ_m. The law is a practical compromise rather than the exact
shape of every cell: with typically 7 to 10 steps per cell, both the logarithm and the
straight line are consistent with the count noise for most cells.

## Results in brief

- **A recipe:** measure the rheobase I_rh and one step I_1 near 2·I_rh with its rate f_1;
  then f(I) ≈ f_1·ln(I/I_rh)/ln(I_1/I_rh) above the rheobase. On the held-out cells half of
  the predicted rates were within a factor of 1.21 of the measured ones.
- **Pre-registered:** four hypotheses, the split and the error measure were fixed before
  the held-out cells were read, and the registration document was fingerprinted
  (SHA-256 `cd36fae6e1542abacfd38bde0ea0acefa4b86eb735f2d786d4941c70a7961cc2`,
  22 October 2026, 16:20 UTC). All four held on the one look at the 700 held-out cells.
- **Against the cells' own models:** median error 0.078 decades for the one-step law,
  0.200 for the cells' published GLIF3 models and 0.301 for GLIF1 (outside the
  registration).
- **Limits, stated in the paper:** the logarithm is the d → 0 limit of a known power
  family, not a new functional form; with 7 to 10 steps per cell it is not distinguished
  from a straight line in most single cells; the zero at the rheobase is close to built in
  by the data. Its advantage appears in prediction across many cells.

## Who did what

In line with the paper's statement on the use of AI:

- **NAI** (No-Ansatz Inference), the system I develop for finding formulas that fit
  given data without fixing their form in advance, found the logarithmic family during
  the exploration (forms such as a + b·ln(x − c), one form for many cells with numbers
  fitted per cell) and the law for k from the cell's properties that was tested in
  check D. The one-parameter law k·ln x is a simplification of the forms it found.
  NAI uses no language model.
- **Claude** (Anthropic), an AI assistant, wrote the analysis scripts, ran the
  exploration and the checks, made the figures and drafted the text of this preprint.
- **I** chose the problem, made the decisions at each step, checked the results and take
  responsibility for the content.

## Checking it

The supplement holds the registration document and its manifest (the fingerprint above
is the SHA-256 of `supplement/registered/ALLEN_FI.manifest`), the working notes and the
scripts as they stood at the registration, the scripts written after it, the list of the
700 held-out cells and the numerical results; its [README](supplement/README.md) says
how to check the fingerprint and rerun the analyses. The registration and the working
notes are in Russian, the language they were written in, with English translations
beside them. The data are not redistributed: the scripts download them from the Allen
Institute's public API. NAI itself is not part of this repository; it is needed only
for the formula search and for check D.

## How to cite

M. Smirnov, The whole f–I curve of a neuron from its rheobase and one current step: a
pre-registered test of a one-parameter logarithmic law on the Allen Cell Types Database,
preprint, 2026, https://github.com/mindscanlabs/NAI-track-record/tree/main/neuron-fi-curves.

## Data and license

The recordings are from the Allen Cell Types Database (© 2015 Allen Institute for Brain
Science; available from https://celltypes.brain-map.org); they are not included here. The
preprint, the registration, the notes and the computed results are under
[CC BY 4.0](../LICENSE-TEXT), the scripts in `supplement/` under [MIT](../LICENSE-CODE).
