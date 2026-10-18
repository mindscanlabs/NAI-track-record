# OEIS: formulas for integer sequences

*October 2026. One frozen build of NAI, one run per sequence. OEIS status as of 18 October 2026.*

NAI was given the first terms of combinatorial sequences from the On-Line Encyclopedia of Integer Sequences (OEIS) and asked for a formula: a closed form, a recurrence or a generating function. Every answer was checked in exact arithmetic against the entry's b-file, on terms NAI had not seen.

## Result in brief

- **Sequences with a known formula: 136 of 140 found, none wrong.**
- **Sequences with no formula in their entry: formulas for 29 of 373,** all holding on every unseen term.
- **79,557 unseen b-file terms** agree with NAI's answers; no answer disagrees with any term.
- **Seven OEIS entries** now contain edits based on NAI's answers, accepted by the OEIS editors; three more are under review. See [oeis-findings](../oeis-findings/).

## Sets

The sets come from text searches on combinatorial enumeration. Three of the four pairs were set aside before development or registered before their first run.

| set | sequences | found | wrong | unseen terms agreeing |
|---|---|---|---|---|
| with a formula, working | 51 | 49 | 0 | 22,189 |
| with a formula, blind | 21 | 21 | 0 | 8,962 |
| with a formula, second blind | 31 | 29 | 0 | 17,324 |
| with a formula, third blind | 37 | 37 | 0 | 22,355 |
| without a formula, working | 101 | 12 | 0 | 4,638 |
| without a formula, blind | 148 | 7 | 0 | 1,886 |
| without a formula, second blind | 92 | 5 | 0 | 701 |
| without a formula, third blind | 32 | 5 | 0 | 1,502 |

## What became of the 29 formulas for sequences without one

Each was checked against the full OEIS entry, including programs and linked files, and against the literature.

| outcome | entries |
|---|---|
| edit accepted into OEIS | A122680, A151318, A180283, A183880, A188350, A321032, A321838 |
| submitted, under review | A052372, A175883, A361245 |
| proved, not yet submitted | A180284, A180285, A183881, A183887 |
| conjectures, not submitted | A057647, A060898, A245002, A321839, A347947 |
| already known in some form | A027439, A157253, A212915, A212916, A233290, A263316, A264765, A264812, A277359, A284230 |

Ten of the 29 were already known, mostly in programs inside the entries that the selection did not read. The proofs and the closed forms derived from NAI's recurrences were done afterwards, by me with the AI assistant Claude, and are not NAI's output. NAI's recurrences for three entries of one family led to the preprint [hardin-sumsets](../hardin-sumsets/).

## Comparison with other systems

There is no shared benchmark for this task, so there is no ranking. Dedicated guessing tools (gfun, Guess, Mathematica's FindLinearRecurrence) find recurrences of this kind from enough terms, and I expect them to do as well on these sequences; I did not run them. Several of the "known" finds above were in fact in OEIS through programs written by its editors. What the result shows is that a general formula-finding system covers this task with no special setup and no wrong answer.

## Conditions and caveats

- **Budget.** About two minutes per sequence on a laptop processor.
- **Seen sets.** All eight sets had been seen by the time this build was frozen; the first runs of the held-out sets, made with earlier builds, found 21 of 21, 27 of 31 and 33 to 37 of 37 sequences with a formula, and 3, 4 and 3 to 5 without, with one wrong closed form in the third set that the current build no longer returns.
- **Selection.** Combinatorial sequences only; number theory was excluded.
- **Conjectures** are verified on every available term, not proved.
