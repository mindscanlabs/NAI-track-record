# Hardin's Arrangements in Which Every Number Is a Sum of Others: Formulas and Sumsets

Mikhail Smirnov, preprint, October 2026. Submitted to the Journal of Integer
Sequences.
[PDF](hardin-sumsets.pdf) · [LaTeX source](hardin-sumsets.tex) · [programs and data](supplement/)

## Abstract

In 2011 Hardin contributed to the OEIS a family of sequences counting
arrangements of residues modulo a fixed integer in which every entry is the sum
of two, or of three, of the other entries; most of them carry only empirical
formulas or conjectures. We show that whether such an arrangement qualifies
depends only on how often each residue occurs, counted up to a small threshold,
which turns the enumeration into a finite sum of exponential generating
functions. Hence every sequence of the family is eventually a sum of polynomials
times exponentials (for ordered arrangements) or a polynomial (for nondecreasing
ones). We give explicit formulas for all twenty-eight sequences of the family,
prove the empirical formulas and conjectures recorded in the OEIS that were
still open, and show that three of the conjectured recurrences hold only from one
step later than stated. We also show that an exponential with base smaller than
the modulus can occur only if some set of that many residues fails to produce
every residue as a sum of two (or three) of its elements, and we conjecture that
this condition is also sufficient; the conjecture holds in all cases computed.

## Results in brief

- The family: OEIS [A183877](https://oeis.org/A183877) to
  [A183892](https://oeis.org/A183892) and [A183897](https://oeis.org/A183897) to
  [A183912](https://oeis.org/A183912), 32 entries (28 sequences and 4 tables).
- Explicit formulas for all 28 sequences, including the 8 that had no formula in
  the OEIS (A183881 to A183883, A183887 to A183891).
- Proofs of the empirical formulas and conjectures recorded in these entries
  that were still open.
- The conjectured recurrences of A183908, A183910 and A183911 hold from
  n > 8, n > 11 and n > 12, one step later than stated in the OEIS.
- A condition on sumsets that every exponential in the formulas must satisfy,
  and a conjecture that it is also sufficient, checked in all 23 cases computed
  (s = 2, q = 2 to 14; s = 3, q = 2 to 11).

## Who did what

In line with the Acknowledgments of the paper:

- **NAI** (No-Ansatz Inference), the system I develop for finding formulas that
  fit given data without fixing their form in advance, guessed linear
  recurrences for A183880, A183881 and A183887 from initial terms; they were checked against further
  terms. This was the starting point of the work.
- **Claude** (Anthropic), an AI assistant, carried out the computations, found
  the profile argument that gives the main theorems, and drafted the proofs and
  the text of this preprint.
- **I** checked the results and take responsibility for the content.

How this work grew out of the NAI findings in the OEIS:
[oeis-findings](../oeis-findings/).

The results are checked by independent programs in the supplement: direct
enumeration for small lengths, comparison with all terms in the OEIS, and the
printed formulas read back from the LaTeX source and evaluated.

Earlier work: R. Israel proved the formulas of A183877 in the OEIS, and his note
for A183912 ([a183912.pdf](https://oeis.org/A183912/a183912.pdf)) uses the same
idea of bounding how often each residue occurs. The paper credits both.

## How to cite

M. Smirnov, Hardin's arrangements in which every number is a sum of others:
formulas and sumsets, preprint, 2026,
https://github.com/mindscanlabs/NAI-track-record/tree/main/hardin-sumsets.

## Data and license

The OEIS entries and b-files in `supplement/data/` were downloaded from the OEIS
in October 2026 and are distributed under the OEIS license
(CC BY-SA 4.0, https://oeis.org/LICENSE). The preprint and the computed data are
under [CC BY 4.0](../LICENSE-TEXT), the programs under [MIT](../LICENSE-CODE).
