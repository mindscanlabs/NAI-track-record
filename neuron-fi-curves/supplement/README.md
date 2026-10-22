# Supplementary material

**The whole f–I curve of a neuron from its rheobase and one current step: a one-parameter logarithmic law, tested on the Allen Cell Types Database with a pre-registered held-out set.** Mikhail Smirnov.

## Contents

| path | what |
|---|---|
| `registered/ALLEN_FI.manifest` | the registration's manifest; its SHA-256 is the fingerprint given in the preprint |
| `registered/docs/prereg/ALLEN_FI.md` | the registration document (Russian original) |
| `registration_EN.md` | its English translation (not covered by the fingerprint) |
| `registered/docs/ALLEN_FI.md` | the working notes as they stood at the registration (Russian original): novelty check, exploration |
| `working_notes_EN.md` | their English translation (not covered by the fingerprint) |
| `registered/bench/allen_fi.py` | data download (Allen API), rows, exploration harness |
| `registered/bench/allen_fi_final.py` | the registered checks A to D |
| `after_registration/bench/allen_fi_paper.py` | the analyses outside the registration: the exponent d per cell, GLIF models, groups |
| `after_registration/bench/allen_fi_figs.py` | the figures |
| `held_out_cells.csv` | the 700 held-out cells (specimen IDs of the Allen Cell Types Database); `in_checks_7_points` marks the 588 with at least seven suprathreshold steps |
| `results/registered_test_checks.json` | the registered checks on the held-out cells |
| `results/glif_test.json`, `results/glif_working.json` | GLIF comparison (outside the registration) |
| `results/groups.json`, `results/boxcox.json` | robustness by group; the exponent d per cell (outside the registration) |

## Language

The registration document and the working notes were written in Russian, and the fingerprint covers these
originals byte for byte, so they are kept unchanged; `registration_EN.md` and `working_notes_EN.md` are their
English translations. Everything else is in English, except two lines of `registered/bench/allen_fi.py` that look
for the Russian result markers in NAI's console output (the script is fingerprinted, so it is not edited).

## Checking the fingerprint

```
sha256sum registered/ALLEN_FI.manifest
# cd36fae6e1542abacfd38bde0ea0acefa4b86eb735f2d786d4941c70a7961cc2
cd registered && sha256sum docs/prereg/ALLEN_FI.md docs/ALLEN_FI.md bench/allen_fi.py bench/allen_fi_final.py
# each digest equals its line in the manifest
```

The manifest also lists the SHA-256 of the two downloaded data files (`cells.json`, `sweeps.json`) and of the
formula-search program's binary. The data are not redistributed here: `allen_fi.py fetch` downloads them from the
Allen Institute's public API (a later download may differ if the database changes). The binary of NAI is not
distributed; it is needed only for the formula search and for check D.

## Running

Python 3, standard library only (the GLIF simulation also uses numpy). The scripts were written for the author's
computer: the data directory is set in `allen_fi.py` (`DATA`), the output in `bench/results/allen_fi/`.

```
python bench/allen_fi.py fetch --out DATA_DIR
python bench/allen_fi_final.py score          # checks A to C (and D with NAI's predictions in place)
python bench/allen_fi_paper.py boxcox
python bench/allen_fi_paper.py groups
python bench/allen_fi_paper.py glif-fetch
python bench/allen_fi_paper.py glif
```

## Data

Allen Cell Types Database, © 2015 Allen Institute for Brain Science. Available from: celltypes.brain-map.org.

License of this material: CC BY 4.0.
