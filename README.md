# Document Intelligence Lab

## Headline verdicts

On the 50-document FUNSD test split, under one pre-registered
protocol (PREREGISTRATION.md, the first commit of this repo):

| Measure | Arm A: Tesseract + rules | Arm B: Gemini vision |
| --- | --- | --- |
| Field precision (micro) | 0.0941 | 0.7865 |
| Field recall (micro) | 0.0490 | 0.2708 |
| Field F1 (micro) | 0.0645 | 0.4029 |
| True positives / predicted / ground truth | 40 / 425 / 816 | 221 / 281 / 816 |
| Median seconds per document | 3.58 | 7.46 |

- H1 CONFIRMED: the vision-LLM arm beats the classical arm on
  field F1 by 0.3384, against a pre-registered line of 0.15.
- H2 CONFIRMED: the classical arm's OCR word error rate is
  0.6942, against a pre-registered line of 0.10.
- H3 INCONCLUSIVE: the classical arm is faster per document
  (median 3.58 s vs 7.46 s, a ratio of 2.08), but not by the
  pre-registered factor of 5, and not by zero either. Read the
  latency caveat below before quoting this either way.

The number that conditions everything else: the vision route
answered only 21 of the 50 documents. The other 29 failed under
the frozen failure rule and scored zero predicted pairs: 27 were
HTTP 429 rate-limit rejections from the access route, 2 were
call timeouts. On the 21 documents the route did answer, its
descriptive F1 is 0.7687, against the classical arm's 0.0628 on
the same documents. The failures are in RESULTS.md and in the
raw records, counted, not dropped.

## Problem

Every document-processing team faces the same fork: build on
classical OCR plus rules you control, or send pages to a vision
model and take the extraction it gives you. The claims made for
both routes are usually benchmark-free. This study measures the
fork on real forms, with both arms scored against the same
human-annotated ground truth, under rules frozen before any run.

## Purpose

Form and document extraction is the core workload of
document-processing roles (the Scotiabank Global AI posting that
motivated this lab names it directly). This repo is the measured
evidence for that workload: what each route gets right, what it
gets wrong, and what it costs in time and reliability.

## Research question and verdict

Question: for information extraction from complex forms, how
does a classical OCR pipeline compare with a vision-LLM route on
accuracy, error character, and cost in time, against the same
ground truth? Verdict: on accuracy the vision route wins by a
wide margin wherever it answers at all; the classical pipeline
as specified here is not close (F1 0.0645). On reliability the
classical pipeline is the predictable one: it processed all 50
documents on local hardware, while the vision route, submitted
in a burst through the existing access route, was rate-limited
into failing 29 of 50. On latency neither registered outcome
holds: the classical arm is about twice as fast at the median,
not five times, and the vision arm's median is itself mostly a
measurement of fast rate-limit rejections (median failed-call
time 7.05 s), so H3 is honestly inconclusive.

## Error character

Arm A fails in three visible ways. Its OCR text on these
degraded fax-era scans is noisy at the character level
("614-~466-S087" for a fax number). Its rule stage then accepts
pairs whose values are whole line remainders, while the ground
truth's values are annotation blocks that often span several
lines, so most of its 425 predictions cannot match exactly under
the frozen normalization. And its word error rate of 0.6942
counts more than misread characters: the reference token order
is annotation order, not reading order, and the two tokenize
numbers and punctuation differently. A diagnostic on document
82092117 (token multiset overlap 133 of 223 against the
reference) suggests ordering and tokenization divergence is a
large share of the distance, alongside genuine character noise.
The 0.6942 stands as the frozen metric defines it; the
diagnostic is context, not a correction.

Arm B fails differently: cleanly, at the service boundary. Its
extraction quality on answered documents is high (precision
0.7865 overall, recall 0.7517 on answered documents) and its
errors are transcription choices, not noise. Its dominant
failure mode in this study is not extraction at all but access:
submitted back to back, the route returned HTTP 429 for most
documents after the first dozen. A production version of this
arm is a pacing and quota problem before it is a modelling
problem. That is a finding about the route as accessed, stated
as such; this study did not re-run under friendlier pacing,
because the pacing was part of the frozen protocol.

## Arms

- Arm A: Tesseract 5.3.4 (user-space install, see DECISIONS.md
  D1) produces one TSV pass per document; a deterministic rule
  stage (colon split, next-line value, wide-gap segment; rules
  R1 to R3 in PREREGISTRATION.md, with amendment A1) emits
  key-value pairs. No learned model.
- Arm B: Gemini 3 Flash Preview, reached only through the
  existing connected Gemini connector (custom.legacy-gemini),
  one vision call per document with a frozen prompt, temperature
  0, one retry on error, failures counted.
- Scoring is shared code (src/common.py): ground-truth pairs
  from FUNSD linking annotations, frozen normalization,
  greedy multiset matching, micro-averaged precision, recall,
  F1; WER by token Levenshtein against annotation word order.

## Reproduce

    sh scripts/fetch_funsd.sh        # downloads FUNSD, verifies SHA-256
    sh scripts/setup_tesseract.sh    # only if no system tesseract exists
    python3 src/run_arms.py --arm both
    python3 scripts/make_results.py  # regenerates RESULTS.md and metrics

The dataset is never committed; derived statistics and
per-document scores are in results/. Re-running Arm B consumes
the shared route's quota and will meet the same rate limits;
its timings and failure counts will differ from this run's.

## Why this matters beyond the lab

Forms are how banks, insurers, and governments ingest the paper
world: account openings, claims, permits, benefits. What gets
automated safely is decided by measured error rates, not by
demos. A pipeline that misreads one token in fifteen can still
be the right choice where a human checks every field, and a
model that reads beautifully but is refused by its own access
route three times in five can stall a digitization programme
that never priced that in. Knowing both numbers, in the open,
is what lets a small team choose the boring, reliable option
where boring and reliable is what the work needs.

## Files

- PREREGISTRATION.md: the frozen protocol (first commit).
- RESULTS.md: generated verdicts and the per-document table.
- AUDIT.md: the author's audit and grade.
- DECISIONS.md: the Tesseract install route, one pre-run rule
  amendment, one harness correction.
- src/: both arms, the shared scorer, the run driver.
- results/: raw per-document records (JSONL), metrics.json,
  the run manifest, the Jev claim-check spec and record.
