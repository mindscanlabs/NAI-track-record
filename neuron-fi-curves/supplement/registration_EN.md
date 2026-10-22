# f–I curves (Allen Cell Types): registration (22 October 2026)

English translation of `registered/docs/prereg/ALLEN_FI.md` (Russian original, which the fingerprint covers).
Paths name files on the author's computer.

Task 4 of the author's list of real problems. Problem statement, novelty check and exploration: `docs/ALLEN_FI.md`
(the working notes, as of the registration, in `registered/docs/`). The test (700 cells, seed 20261022) has never
been looked at; this is its first and only look.

## Data
Allen API, downloaded on 22 October 2026 (`D:/Claude/nai-data/allen_ct`; cells.json SHA-256 4b6c0d83…700f,
sweeps.json 7cd08739…123e): 2,333 cells, 58,585 Long Square sweeps. Rows: `bench/allen_fi.py` (current at or above
the rheobase, with spikes; x = I/I_th). Checks: cells with at least 7 suprathreshold points.

## Protocol (`bench/allen_fi_final.py`)
- A. Continuation of the curve: per-cell forms fitted on the lower 60 % of the currents predict the upper 40 %
  (line a + b·x; a + b·ln x; k·ln x; a + b·ln(x − c); a − b·exp(−x/c); a + b·√(x − 1); a + b·(x − 1)^p).
- B. The whole curve from the rheobase and one sweep (nearest x = 2, x > 1.2): k·ln x, k = f1/ln x1, against the
  line through the threshold f1·(x − 1)/(x1 − 1).
- C. The zero of the logarithmic law: x0 = exp(−a/b) of a + b·ln x fitted to the cell's whole curve.
- D. k from the cell's properties (τ, Ri, I_th, spiny, human): the law found by NAI against a log-linear one (least
  squares); NAI v21 (`bench/results/v21/nai_cli_v21.exe`), 300 s, seed 1, table `ktrain.csv` (σ: the RMS of the
  log-linear law's residuals).
- Error |lg(f̂/f)|; a prediction below 0.5 Hz is counted as 0.5 Hz.
- Run: `allen_fi_final.py ktable`; NAI `--data ktrain.csv --seconds 300 --seed 1 --predict kpoints.csv nai_k.pred`;
  `allen_fi_final.py score`.

## Hypotheses
- **H1.** A: for a + b·ln x both the mean and the median error are lower than for the line a + b·x.
- **H2.** B: the median error of k·ln x is below 0.85 times the median of the line through the threshold.
- **H3.** C: the median x0 lies in [0.93; 1.03]: the law's zero at the rheobase.
- **H4.** D: the mean |Δ lg k| of NAI's law is lower than that of the log-linear law.

Expectation from the exploration (splits 1 / 2): H1 yes (0.140/0.055 and 0.134/0.062 against 0.147/0.074 and
0.139/0.078); H2 yes (0.087/0.090 against 0.125); H3 yes (0.975/0.979); H4 yes (0.251/0.241 against 0.261/0.257).
Exploration: 15 variants of NAI and of forms (set-ups 1 and 2, targets f and lg f, limits on the constants, the law for k).

## Deviations
A harness failure: fix it, rerun with the same program, record it in `docs/prereg/ALLEN_FI-deviation.md`.
No changes to the program, the data or the rules after the registration.
