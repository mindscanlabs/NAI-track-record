<p align="center">
  <img src="nai_logo.png" alt="NAI logo" width="320">
</p>

# NAI-track-record

The track record of the NAI (No-Ansatz Inference) system: results that began with
formulas found by NAI, and what has happened to them since. For each result the
documents say whether it has been proved, whether it has been accepted by the
editors of the OEIS or submitted to a journal, and what is still open. Preprints
and related documents on these results are collected here.

NAI is a system I develop for finding formulas that fit given data without
fixing their form in advance. NAI does not use language models. Its source code
and method are not part of this repository; each document says exactly which of its
results came from NAI and which were obtained afterwards, and by whom.

## Documents

| date | document | folder | status |
|---|---|---|---|
| October 2026 | Hardin's Arrangements in Which Every Number Is a Sum of Others: Formulas and Sumsets | [hardin-sumsets](hardin-sumsets/) | preprint; submitted to the Journal of Integer Sequences |
| October 2026 | OEIS findings that began with NAI (history and status of the edits) | [oeis-findings](oeis-findings/) | updated as the OEIS reviews the edits |

Each paper folder holds the document (PDF and LaTeX source) and a `supplement`
with the programs and data needed to check it.

## Use of AI assistants

Some of the work in these documents was done with an AI assistant (Claude,
Anthropic). Its role is stated in each document and in the folder's README,
next to the role of NAI.

## License

- Texts (documents, READMEs, preprints in PDF and LaTeX) and computed data
  (profiles, formulas, check reports): [CC BY 4.0](LICENSE-TEXT).
- Programs (the `programs` folders of the supplements): [MIT](LICENSE-CODE).
- Data taken from the OEIS (entries and b-files in the `data` folders): the OEIS
  license, [CC BY-SA 4.0](https://oeis.org/LICENSE).

## Contact

Mikhail Smirnov, lab@mindscan.org
