# Supplement: programs and data

For the preprint *Hardin's Arrangements in Which Every Number Is a Sum of Others:
Formulas and Sumsets* (M. Smirnov, October 2026; source `../hardin-sumsets.tex`).
Everything below runs from this folder, and `build_tex.py` reproduces
`../hardin-sumsets.tex` byte for byte.

## Requirements

- A C++17 compiler (tested with g++ 15, MSYS2 UCRT64).
- Python 3 with sympy (tested with Python 3.14, sympy 1.14).

## Layout

| path | contents |
|---|---|
| `programs/oeis_profiles.cpp` | enumerates all $(s+2)^q$ profiles, tests them with Lemma 3, prints the histogram of valid profiles by the numbers of residues in each class (Section "Computation") |
| `programs/oeis_hardin_family.py` | exact formulas for all 28 sequences from the histograms (Theorems 5 and 6), checked against the OEIS data and against the formulas recorded in the OEIS |
| `programs/oeis_hardin_format.py` | the closed forms of the arrangement sequences in the printed form of the paper, each checked on 80 values |
| `programs/oeis_hardin_mod_proof.py` | the original stand-alone proof for A183881 and A183887 (profiles enumerated in Python) |
| `programs/sumset_check.py` | Section "Which exponentials occur": the exponentials that occur versus $K(q,s)$; checks Theorem 7, Corollary 8 and Conjecture 12 |
| `programs/brute_force_check.py` | direct enumeration of words for small lengths against the b-files and the $q = 2$ columns |
| `programs/build_tex.py` | builds the LaTeX source from the verified formula files (writes `rebuilt/hardin-sumsets.tex`) |
| `programs/check_tex.py` | reads the 28 formulas back from the printed LaTeX and checks them against the exact counts, including that each fails for all smaller $n$ |
| `programs/oeis_hardin_submit_texts.py` | the texts of the corresponding OEIS submissions |
| `data/profiles/hist_q{q}_s{s}.txt` | histograms of valid profiles: $s = 2$, $q = 2..14$; $s = 3$, $q = 2..11$. Each line: numbers of residues with profile value $0, 1, \ldots, s+1$, then the number of valid profiles |
| `data/profiles/family_report.json`, `family_run.txt` | the formulas and all checks against the OEIS |
| `data/profiles/arr_formulas.json`, `nd_formulas.json` | the formulas of Theorems 9 to 11, as printed |
| `data/profiles/bases_table.txt` | Table 2 (exponentials and degrees of $P_k$) |
| `data/profiles/hardin_mod_proof.txt` | output of `oeis_hardin_mod_proof.py` |
| `data/bfiles/` | the b-files of all 32 entries of the family and of A000295, A005803 (downloaded from the OEIS, October 2026); A183902 and A183903 have no separate b-file in the OEIS; their files are the ones the OEIS synthesizes from the terms in the entries |
| `data/oeis_entries/` | the OEIS entries of the family in text format (fetched 2026-10-18), including all formulas, comments, and links that the paper refers to |

## Reproducing the paper

From `programs/`:

```
mkdir -p ../rebuilt
g++ -O2 -std=c++17 -o ../rebuilt/oeis_profiles.exe oeis_profiles.cpp
../rebuilt/oeis_profiles.exe 7 2 > ../rebuilt/hist_q7_s2.txt     # compare with ../data/profiles/hist_q7_s2.txt
python oeis_hardin_family.py > ../rebuilt/family_run.txt          # rewrites ../data/profiles/family_report.json
python oeis_hardin_format.py A183877 A183878 A183879 A183880 A183881 A183882 A183883 A183885 A183886 A183887 A183888 A183889 A183890 A183891
python build_tex.py                                               # ../rebuilt/hardin-sumsets.tex, identical to ../../hardin-sumsets.tex
python check_tex.py                                               # 28 formulas, all correct
python sumset_check.py                                            # theorem and conjecture in all 23 cases
python brute_force_check.py                                       # direct enumeration for small lengths
```

Timings (one core): each histogram for $q \le 9$ takes about a second; $q = 11$,
$s = 3$ about 40 seconds; $q = 14$, $s = 2$ about three minutes.
`oeis_hardin_family.py` takes a few minutes, `check_tex.py` about ten.

## Notes

- Positions are distinct: a word is $s$-covered if every entry equals the sum of
  the entries at $s$ distinct other positions (the reading confirmed by
  `brute_force_check.py`).
- R. Israel's proof for A183912 is referred to in the paper by its OEIS link
  (https://oeis.org/A183912/a183912.pdf); it is not part of this folder.
- Who did what is stated in the Acknowledgments of the paper and in `../README.md`.
- The OEIS data in `data/` is distributed under the OEIS license (CC BY-SA 4.0).
