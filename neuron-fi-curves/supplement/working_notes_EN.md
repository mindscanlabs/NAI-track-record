# Frequency–current curves of neurons (Allen Cell Types; IDEAS §18, task 4)

English translation of `registered/docs/ALLEN_FI.md` (Russian original, which the fingerprint covers): the working
notes as they stood at the registration. Paths name files on the author's computer; "IDEAS §18" is the author's
list of tasks. The translator's notes are in square brackets.

## Goal (set by the author, 22 October 2026)
Find something new and useful rather than test NAI as on a benchmark: try set-ups and settings of the program on
the working part; the test once, after the registration.

Question: do the f(I) curves of thousands of real cells fall on one common curve in dimensionless variables, and
what is its shape? Use: from the threshold I_th and the membrane time constant τ (cheap measurements), predict the
whole curve of a cell: fewer experiments, parameters for network models.

## Novelty check (22 October 2026)
- Allen describes the curve by one number, the slope of a straight line (`ef__f_i_curve_slope`).
- Near threshold the curve is a power law (Hansel & van Vreeswijk 2002; Roxin et al., J. Neurosci. 2011,
  "On the distribution of firing rates…"). [The first reference is given as in the notes; it was not verified and
  is not cited in the preprint.] The LIF model: f = 1/(t_ref + τ·ln(x/(x − 1))), x = I/I_th.
- The search found no fits of nonlinear forms to the Allen data across all cell types and no check of the collapse
  f·τ = G(I/I_th) on real cells (a 2024 preprint fitted functions φ(V) to Allen data; the form was not specified).

## Data
Allen API (`bench/allen_fi.py fetch`, 22 October 2026, `D:/Claude/nai-data/allen_ct`): 2,333 cells (1,344 mouse and
289 human in the working part), 58,585 Long Square sweeps (current, duration 1 s, number of spikes). A row: a cell
and a current not below the rheobase (`ef__threshold_i_long_square`) with spikes; f is spikes per second, the mean
over repeats. Test: 30 % of the cells (700, seed 20261022); working part: 1,633. Exploration: internal splits of the
working part (seed 1 or 2, checked on 30 % of the cells).

## First observations (working part)
- Most cells have 6 to 10 points above threshold; the curves are more often concave (saturating): 956 against 344
  convex and 260 nearly straight (cells with at least 5 points).
- **The collapse in τ holds:** in the power law lg f = a + b·lg(x − 1 + 0.05) + c·lg τ the fitted exponent is
  c = −1.09 and −1.05 (splits 1 and 2): the rate is almost exactly inversely proportional to τ.
- The LIF form does not fit (0.74 dex against 0.33 for the power law with τ); the cell class (spiny or not), the
  species and the input resistance add almost nothing to the baseline model.
- The errors are large near threshold (x < 1.5: 0.39 to 0.45 dex): at the rheobase the rate is almost always 1 Hz
  (one spike).

## NAI exploration (22 October 2026, working part)
**Set-up 1: one table of all cells** (x, τ, [Ri, class] → lg f, a single σ = 0.5 dex): NAI v21 declares "solved"
formulas such as lg f = x − 1 + (273 − 270√x + 164·ln x)/τ. With σ = 0.5 dex almost any formula passes as "within
the noise"; at x ≥ 3 the error is 0.9 to 1.5 dex. The scatter here is the individuality of the cells, not
measurement noise: this set-up is unfit for finding the shape.

**Set-up 2: the shape of the curve:** group mode, a group is a cell (one form, numbers per cell), count noise
(σ(lg f) = 1/(ln 10·√n)); NAI searches over 60 cells, and the form is chosen by the highest currents of each cell
(`--extrap x`). Check: for about 400 checked cells the numbers of the form are fitted on the lower 60 % of the
currents and the upper 40 % are predicted (continuation of the curve: fewer sweeps). Error |lg(f̂/f)|,
split 1 / split 2:

| model | mean | median |
|---|---|---|
| per-cell line, f = a + b·x | 0.147 / 0.139 | 0.074 / 0.078 |
| square root, f = a + b·√(x − 1) | 0.194 / 0.184 | 0.110 / 0.110 |
| power law in lg | 0.228 / 0.219 | 0.122 / 0.142 |
| NAI, lg f, constants unrestricted | 0.198 / 0.273 | 0.110 / 0.132 |

NAI's form (split 1): lg f = a − b·exp(exp(c/x)), an approach to saturation; but the curves keep rising at the
highest currents, and the straight line continues them better.

[The notes, as fingerprinted, end here. The exploration of the logarithmic family that led to the registered
checks (targets f instead of lg f, the forms a + b·ln(x − c) and a + b·ln x, the zero x₀, the law for k) is
summarised by the expected results in the registration document: `registration_EN.md`, "Expectation from the
exploration".]
