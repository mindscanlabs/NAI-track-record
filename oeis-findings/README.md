# OEIS findings that began with NAI

Status as of 2026-10-23.

This is the history of a set of contributions to the
[OEIS](https://oeis.org) that started from formulas found by the NAI (No-Ansatz
Inference) system, which I develop for finding formulas that fit given data
without fixing their form in advance. For each entry it shows:

- **NAI**: what NAI found from the terms of the sequence alone (a recurrence or a
  generating function);
- **Claude**: what was done afterwards with the AI assistant Claude (Anthropic):
  closed forms, proofs, generalizations;
- **status** in the OEIS.

I submitted all edits to the OEIS under my name. Nesting in the trees means "led
to".

Statuses:

- **accepted**: the edit is in the OEIS;
- **pending**: submitted, under review by the OEIS editors;
- **not yet submitted**: ready, or still being prepared;
- **already known**: what was found turned out to be in the entry already, or in
  earlier work.

## 1. The Hardin family

The three recurrences found by NAI for A183880, A183881 and A183887 led to a
solution of the whole family A183877 to A183912 (32 entries: 28 sequences and 4
tables) and to a preprint, submitted to the Journal of Integer Sequences:

> M. Smirnov, *Hardin's Arrangements in Which Every Number Is a Sum of Others:
> Formulas and Sumsets*, preprint, October 2026.
> [PDF](../hardin-sumsets/hardin-sumsets.pdf) ·
> [LaTeX source](../hardin-sumsets/hardin-sumsets.tex) ·
> [programs and data](../hardin-sumsets/supplement/) ·
> [about the preprint](../hardin-sumsets/)

```
A183880  NAI: recurrence | Claude: closed form, g.f. | accepted (as conjectures)
└── A183881, A183887  NAI: recurrences | Claude: closed forms, proof | not yet submitted
    └── The Hardin family, 32 entries  Claude: proof for all 28 sequences
        ├── Words, sum of two others
        │   ├── A183877  empirical formula (Kotesovec), conjectures (Barker): proved by Israel (2018), already known
        │   ├── A183878  empirical formula (Kotesovec), conjectures (Barker): proved
        │   ├── A183879  empirical formula (Kotesovec), conjectures (Barker): proved
        │   ├── A183880  conjectures (accepted above): proved
        │   ├── A183881  new formula, proved
        │   ├── A183882  new formula, proved
        │   ├── A183883  new formula, proved
        │   └── A183884  table: every column covered
        ├── Words, sum of three others
        │   ├── A183885  empirical formula (Kotesovec), conjectures (Barker): proved
        │   ├── A183886  empirical formula (Kotesovec), conjectures (Barker): proved
        │   ├── A183887  new formula, proved
        │   ├── A183888  new formula, proved
        │   ├── A183889  new formula, proved
        │   ├── A183890  new formula, proved
        │   ├── A183891  new formula, proved
        │   └── A183892  table: every column covered
        ├── Nondecreasing arrangements, sum of three others
        │   ├── A183897 ... A183901  empirical formulas (Hardin), conjectures (Barker): proved
        │   ├── A183902, A183903  empirical formulas (Hardin): proved
        │   └── A183904  table: every column covered
        ├── Nondecreasing arrangements, sum of two others
        │   ├── A183905 ... A183907, A183909  empirical formulas (Hardin), conjectures (Barker): proved
        │   ├── A183908, A183910, A183911  formulas proved; Barker's recurrences hold one step later than stated
        │   └── A183912  table; Israel (2018): columns are eventually polynomials, already known; generalized to all s
        ├── Theorem on exponentials  Claude: k^n (k < q) can occur only if some set of k residues
        │   fails to cover Z_q by s-fold sums; the converse is a conjecture, true in all 23 cases computed
        └── Preprint "Hardin's Arrangements in Which Every Number Is a Sum of Others:
            Formulas and Sumsets", submitted to the Journal of Integer Sequences
```

In numbers:

- the empirical formulas and conjectures in 18 entries are proved for the first
  time (A183877 had already been proved by Israel); in 3 of them the ranges of the
  conjectured recurrences are corrected (below);
- the conjectures accepted in A183880 are proved;
- 8 sequences that had no formula get proved formulas (A183881 to A183883,
  A183887 to A183891);
- in 3 entries (A183908, A183910, A183911) the conjectured recurrences hold from
  one step later than stated.

Apart from the conjectures in A183880, the OEIS edits for this family are not
yet submitted; all of it is in the
[preprint](../hardin-sumsets/hardin-sumsets.pdf).

## 2. Other branches

```
A180283  NAI: recurrence | Claude: closed form, proof | accepted
└── A180284, A180285  Claude: closed forms, proof (special cases of Heinz's formula in A180281) | not yet submitted

A321838  NAI: recurrence | Claude: g.f. (accepted); then proof and a new formula | accepted
└── A213291  Claude: g.f., follows from the g.f. of A321839 | not yet submitted
        ↑
A321839  NAI: algebraic g.f. (conjecture) | not yet submitted

A052372  NAI: g.f. | Claude: proof (Burnside's lemma), explicit numerator, asymptotics | pending
└── A052373  Claude: g.f. by the same argument, proof | not yet submitted

A122680  NAI: algebraic equation for the g.f. | Claude: proof | accepted
├── A122680 b-file  Heinz extended it from 1000 to 1075 terms by solving this equation
└── A175883  NAI: g.f. | Claude: proof with the same kernel | accepted

A151318  NAI: recurrence (already known), then g.f. | Claude: proof | accepted

A361245  NAI: g.f., recurrence | Claude: proof, the simpler form C = 1 + x*C^3 + x^2*C^5, explicit sum | accepted

A188350  NAI: recurrence | Claude: g.f. | accepted (as conjectures)

A321032  NAI: recurrence | Claude: g.f. | accepted (as conjectures)

A263316, A212915, A212916  NAI: recurrences | already known (they were in the programs of these entries)
```

## Notes on the links

- **A183880 to A183881, A183887 to the Hardin family.** NAI found recurrences of
  the same kind as for A183880 for the neighboring entries A183881 and A183887.
  The proof for them, by counting how often each residue occurs up to a small
  threshold, solved the whole family. Israel had used the same idea for one table
  of the family (A183912, s = 2); the [preprint](../hardin-sumsets/hardin-sumsets.pdf) credits him and extends it.
- **A180283 to A180284, A180285.** The same difference formula for the maxima 4
  and 5.
- **A321838 to A213291, from A321839.** The argument that proved the g.f. of
  A321838 links A321839 with A213291, so a g.f. of A321839 gives one for A213291.
- **A052372 to A052373.** The proof by Burnside's lemma for 6 x 6 matrices carries
  over to 7 x 7.
- **A122680 to A175883.** Both sequences have the same kernel: the g.f. of A122680
  is a sum of residues at the small roots of the kernel, and the g.f. of A175883
  is the product of these roots.

## Entries

| entry | status | |
|---|---|---|
| [A183880](https://oeis.org/A183880) | accepted (as conjectures); proof not yet submitted | [history](https://oeis.org/history?seq=A183880) |
| [A183877](https://oeis.org/A183877) ... [A183912](https://oeis.org/A183912) | not yet submitted; see the [preprint](../hardin-sumsets/hardin-sumsets.pdf) | |
| [A180283](https://oeis.org/A180283) | accepted | [history](https://oeis.org/history?seq=A180283) |
| [A180284](https://oeis.org/A180284), [A180285](https://oeis.org/A180285) | not yet submitted | |
| [A321838](https://oeis.org/A321838) | accepted | [history](https://oeis.org/history?seq=A321838) |
| [A321839](https://oeis.org/A321839), [A213291](https://oeis.org/A213291) | not yet submitted | |
| [A052372](https://oeis.org/A052372) | pending | |
| [A052373](https://oeis.org/A052373) | not yet submitted | |
| [A122680](https://oeis.org/A122680) | accepted | [history](https://oeis.org/history?seq=A122680) |
| [A175883](https://oeis.org/A175883) | accepted | [history](https://oeis.org/history?seq=A175883) |
| [A151318](https://oeis.org/A151318) | accepted | [history](https://oeis.org/history?seq=A151318) |
| [A361245](https://oeis.org/A361245) | accepted | [history](https://oeis.org/history?seq=A361245) |
| [A188350](https://oeis.org/A188350) | accepted (as conjectures) | [history](https://oeis.org/history?seq=A188350) |
| [A321032](https://oeis.org/A321032) | accepted (as conjectures) | [history](https://oeis.org/history?seq=A321032) |
| [A263316](https://oeis.org/A263316), [A212915](https://oeis.org/A212915), [A212916](https://oeis.org/A212916) | already known | |

## What this does and does not show

- NAI gave the starting points: every formula marked "NAI" above was found from
  the terms alone, and none of them has turned out to be wrong so far.
- The proofs, the closed forms derived from recurrences, and the theorem on the
  Hardin family were done afterwards with Claude, not by NAI.
- There is no comparison with other tools here: some of these recurrences could
  also be found by standard guessing software.
