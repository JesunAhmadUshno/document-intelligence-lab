# Pre-registration: classical OCR extraction vs a vision-LLM route on real forms

Locked before any measured run exists. The commit that adds this
file precedes every result in this repository; git history proves
the order. Any change to this file after locking is an amendment
and must be recorded in DECISIONS.md with its reason, before the
runs it affects.

## Research question

For information extraction from complex forms and documents, how
does a classical OCR pipeline compare with a vision-LLM extraction
route on accuracy, error character, and cost in time, when both
are scored against the same human-annotated ground truth?

## Machine of record

All runs happen on one named machine: the Muse VM, hostname
htch-runtime (Linux 7.0.0-43-generic, AMD EPYC 9D25, 4 vCPUs,
7 GiB RAM), Python 3.12.3. No number from any other machine is
reported in this study. Arm B's model runs remotely by definition;
its measured time is the full call wall time from this machine,
which is the cost a user of the route actually pays.

## Corpus

FUNSD (Jaume, Ekenel, Thiran, 2019), the public form-understanding
corpus of 199 real scanned forms with entity-level annotations:

- dataset.zip from https://guillaumejaume.github.io/FUNSD/dataset.zip
- 16,838,830 bytes
- SHA-256: c31735649e4f441bcbb4fd0f379574f7520b42286e80b01d80b445649d54761f
- Split as published: training_data 149 documents, testing_data
  50 documents. Scoring uses the 50 test documents only. The
  training split is not used by either arm (neither arm learns).
- The dataset itself is never committed to this repository.
  Derived statistics and per-document scores only.

## The task (frozen)

Extract key-value field pairs from each test document.

Ground-truth pairs come from the FUNSD annotations. Each
annotation file holds a "form" list of blocks; a block has an id,
a label (header, question, answer, other), a text, and linking
pairs. The ground-truth pair set of a document is: for every
linking pair whose two blocks are one question block and one
answer block, the pair (question block text, answer block text),
deduplicated. Links between any other label combination are
ignored, as are unlinked blocks.

### Matching rule (frozen)

Normalization N(s): apply Unicode NFKC, lowercase, replace every
maximal run of characters that are not letters or digits with a
single space, strip leading and trailing spaces.

A predicted pair (k, v) is a true positive if the multiset of
normalized ground-truth pairs contains (N(k), N(v)); each
ground-truth pair can be matched at most once. Predictions are
tested in the arm's output order and consume matches greedily.

Precision = TP / (number of predicted pairs). Recall = TP /
(number of ground-truth pairs). F1 = 2 * P * R / (P + R), with
F1 = 0 if P + R = 0. Metrics are micro-averaged: pairs are pooled
across all 50 test documents before P, R, and F1 are computed.
Per-document P, R, F1 are reported in the raw table alongside.

## Arm A: classical pipeline (frozen)

- OCR engine: Tesseract 5.3.4 (tesseract-ocr 5.3.4-1build5,
  Ubuntu package, user-space install; language data eng,
  tesseract-ocr-eng 4.1.0). OEM and PSM at Tesseract defaults
  (OEM 1, PSM 3). One invocation per document, TSV output.
- The extraction stage consumes only that TSV. Words are TSV
  level-5 rows with conf >= 0. Lines are keyed by (block_num,
  par_num, line_num) in TSV emission order; a line's text is its
  words joined by single spaces; a line's box is the union of its
  word boxes.
- Deterministic extraction rules, applied in reading order. A
  line consumed as a key or as a value is never reused.
  - R1 (same-line colon): if a line's text contains ':' and the
    part before the first ':' has 1 to 6 words, at most 45
    characters, and at least one letter, it is a key. If the part
    after the ':' is non-empty, it is the value and the pair is
    emitted.
  - R2 (next-line value): if a line ends with ':' and its text
    without the trailing ':' has at most 8 words, at most 60
    characters, and at least one letter, it is a key (unless R1
    already emitted it with a value). Its value is the first
    later line within the next 3 line positions that is not
    itself a key under R1 or R2 and has non-empty text. If none
    exists, no pair is emitted for this key.
  - R3 (right segment): for a line not consumed and not a key
    under R1 or R2, find the largest horizontal gap between
    consecutive words. If that gap is at least 40 pixels and at
    least 2.0 times the line's median inter-word gap, and the
    left segment has 1 to 6 words, at most 45 characters, and at
    least one letter, and the right segment is non-empty, emit
    (left segment, right segment).
- Predicted pairs are deduplicated per document on their
  normalized (key, value). Keys must contain a letter; values
  must be non-empty.
- OCR word error rate: the reference token sequence of a
  document is the words of its annotation blocks, blocks in
  "form" order, words in listed order. The hypothesis token
  sequence is the TSV words in emission order. Tokenization for
  WER: lowercase, split on whitespace (FUNSD word texts are taken
  as single tokens, splitting any that contain spaces). WER is
  the Levenshtein edit distance over token sequences divided by
  the reference token count, micro-averaged over the test set
  (total edits / total reference tokens). Per-document WER is
  reported alongside.
- Arm A time per document: wall time of the Tesseract subprocess
  plus the extraction stage, measured in-process.

## Arm B: vision-LLM route (frozen)

- Route: the existing connected Gemini connector
  (custom.legacy-gemini). Calls follow the connector's documented
  pattern: POST to generativelanguage.googleapis.com
  /v1beta/models/gemini-3-flash-preview:generateContent with the
  credential attached by the dynamic-credentials helper under
  the stored connector name custom.gemini. No other host, no
  other provider, no new key or account.
- Request per document: one call. Parts: the document image as
  inline_data (image/png, base64) and the frozen prompt below.
  generationConfig temperature 0.
- Frozen prompt, verbatim:
  "You are extracting fields from a scanned form. List every
  field on the form as a JSON array of objects with exactly two
  keys: "question" and "answer". The question is the printed
  field label, transcribed exactly as printed, including any
  trailing colon. The answer is the value belonging to that
  label, transcribed exactly as it appears. Include only fields
  where both a label and a value are present. Do not invent
  values. Do not include headers, titles, or body text that are
  not field labels with values. Respond with the JSON array
  only, no other text."
- Parsing: strip Markdown code fences if present, then parse
  JSON. The result must be a list of objects; a predicted pair
  is (question, answer) for each object where both are strings
  and non-empty after stripping. Anything else is a parse
  failure for that document.
- Failures: on an HTTP error or timeout, exactly one retry after
  5 seconds. A document that still fails, or whose response does
  not parse, is a failed document: it contributes zero predicted
  pairs, stays in every denominator, and is counted in the
  failure count. Failures are reported, never dropped.
- Arm B time per document: wall time of the call (including the
  retry, if one happens) plus parsing.
- Calls per document are counted and reported.

## Hypotheses (frozen, with pass lines)

Verdict vocabulary: CONFIRMED, REFUTED, INCONCLUSIVE.

### H1: the vision-LLM arm wins on accuracy

CONFIRMED if F1(Arm B) - F1(Arm A) is at least 0.15.
REFUTED if F1(Arm B) - F1(Arm A) is at most 0.00.
INCONCLUSIVE between.

### H2: the classical noise floor

CONFIRMED if Arm A's micro-averaged WER is at least 0.10.
REFUTED if Arm A's micro-averaged WER is below 0.05.
INCONCLUSIVE between.

### H3: the classical arm wins on latency

Let tA and tB be the median per-document wall times of Arm A and
Arm B over the 50 test documents. CONFIRMED if 5 * tA is at most
tB (the classical arm is at least 5 times faster). REFUTED if tA
is at least tB (the classical arm is not faster at all).
INCONCLUSIVE between.

## Measurement protocol (frozen)

- Every test document is processed by both arms. Each arm writes
  one JSONL record per document: document id, predicted pairs,
  seconds, and arm-specific fields (Arm B: call count, failure
  flag; Arm A: OCR word count).
- Timing spread is reported as median, mean, and interquartile
  range per arm.
- RESULTS.md is generated by scripts/make_results.py from the
  raw JSONL records; verdicts are computed by that script from
  the frozen pass lines above, never typed by hand.
- With no runs, the results generator produces an awaiting-runs
  RESULTS.md that cannot be mistaken for results.
- No number is reported from any document outside the published
  test split, and no document is excluded for being hard, blank,
  or a failure for either arm.
