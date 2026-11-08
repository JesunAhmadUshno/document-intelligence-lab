# Audit

Author's audit of this build against the programme charter.
State at audit time: complete. Both arms ran on all 50 FUNSD
test documents under the frozen protocol; RESULTS.md and
results/metrics.json are generated from the raw records; the
repository is public with CI green.

## Charter gates

1. Pre-registration before results. PREREGISTRATION.md is the
   first content commit (0774bfd), written before any code or
   run existed. Git history shows the order.
2. Numbers come from scripts. Every number in README.md and
   RESULTS.md is computed by scripts/make_results.py from
   results/arm_a.jsonl and results/arm_b.jsonl via the shared
   scorer in src/common.py. Verdicts are computed from the
   frozen pass lines by that script, never typed by hand.
3. Failures are data, not inconveniences. Arm B failed 29 of 50
   documents (27 HTTP 429 rate-limit rejections, 2 timeouts).
   Every failure is a raw record with its error string, scored
   as zero predicted pairs, and kept in every denominator,
   exactly as the pre-registration froze it. No document was
   excluded for being hard, and Arm B was not re-run under
   gentler pacing to improve its numbers: the burst submission
   and the one-retry rule were the protocol.
4. Corpus integrity. FUNSD dataset.zip, SHA-256
   c31735649e4f441bcbb4fd0f379574f7520b42286e80b01d80b445649d54761f,
   verified at download by scripts/fetch_funsd.sh; the dataset
   is never committed (data/ is gitignored). Scoring covers the
   published 50-document test split only.
5. Arms as registered. Arm A is the real Tesseract 5.3.4 (see
   DECISIONS.md D1 for the user-space install) plus the frozen
   rules; Arm B used only the existing connected Gemini route
   (custom.legacy-gemini), the model it serves
   (gemini-3-flash-preview, confirmed in response metadata and
   results/run_manifest.json), the frozen prompt, temperature 0.
   No new key, account, or provider was created.
6. Spend. Zero. Tesseract is open source, the corpus is public,
   and the Gemini calls went through the user's existing
   connected route.
7. Jev claim_check. Model jev-1.13.0, question "supported",
   noul 0.47. Under the claim_check bands (clear at 0.85 or
   above, block at 0.10 or below, review between), the route is
   REVIEW. The claim was therefore hand-verified figure by
   figure against results/metrics.json and the raw JSONL: F1
   values 0.4029 and 0.0645 and their 0.3384 difference; WER
   0.6942 as 6060 edits over 8729 reference tokens; medians
   3.58 s and 7.46 s and the H3 arithmetic (5 x 3.58 = 17.9
   exceeds 7.46; 3.58 is below 7.46); the 29 failures split as
   27 HTTP 429 and 2 timeouts across 89 total calls; the
   answered-subset descriptors (21 documents, 294 ground-truth
   pairs, Arm B F1 0.7687, Arm A F1 0.0628). Every figure in the
   claim agrees with the records. Spec and response are in
   results/jev-claim-spec.json and results/jev-claim-check.json
   (1102 input tokens, 20 output tokens).

## Deviations and incidents on record

- DECISIONS.md D1: Tesseract is a user-space install (Ubuntu
  packages unpacked under .tools/), because this VM ships no
  system Tesseract and no sudo. The arm is still the named
  engine, version recorded in the run manifest.
- Amendment A1 (before any measured run): R2's value search
  stopped at the first intervening key line, after a unit test
  showed the original text could steal a later key's value.
  Recorded in DECISIONS.md; no run precedes it.
- DECISIONS.md D2: during the Arm B run, one call sat in flight
  far past the intended timeout (a urllib socket timeout does
  not bound a slow-drip response through the proxy). The client
  gained a hard 180-second per-attempt deadline enforced on a
  daemon thread; exceeding it is the timeout the frozen failure
  rule already describes. The stuck attempt produced no record;
  the affected document's recorded outcome (two deadline
  expiries, counted failed) came from the corrected client.
- The HTTP 429 pattern: successes and failures interleave early
  (first failure at document position 2, a timeout), and
  rejections dominate from about the thirteenth document on.
  This is reported as the route's behavior under burst
  submission, not smoothed into a smaller failure count.

## Interpretation notes (not protocol outputs)

- The WER reference order is FUNSD annotation order, which is
  not reading order, and the annotation tokenization splits
  numbers and punctuation that Tesseract emits as single tokens.
  A one-document diagnostic (82092117: token multiset overlap
  133 of 223) indicates ordering and tokenization divergence is
  a large share of the 0.6942, alongside genuine character
  noise on degraded scans. H2's verdict is unaffected (the line
  was 0.10), but readers should not quote 0.6942 as a pure
  character-error rate.
- Arm B's all-document median time (7.46 s) is dominated by
  fast rejections (median failed-document time 7.05 s, two
  quick 429 responses plus the frozen 5-second pause). The
  answered documents' median call time is 23.32 s. H3's
  INCONCLUSIVE verdict is computed exactly as frozen, over all
  50 records per arm; as a pure speed comparison it is weak
  evidence, and the README says so.

## Grade: 6,000 of 10,000

Deductions, itemized:

- 1,500: Arm B coverage. The route answered 21 of 50 documents;
  the study's central comparison is therefore rate-limit-bound.
  The failures are honestly counted and are themselves a
  finding, but nearly three fifths of the vision arm's cells
  are access rejections, not extractions, and no verdict here
  should be read as a clean evaluation of the model's ceiling.
- 700: the H3 latency measurement is contaminated by those
  rejections (fast failures pull Arm B's median down), so the
  latency verdict carries weak information despite being
  computed exactly as registered.
- 600: Arm A's extractor is one minimal deterministic ruleset.
  Its results bound that ruleset, not classical OCR pipelines
  in general; the README names this, and the bound still
  narrows what the study proves.
- 500: the frozen WER counts reading-order and tokenization
  divergence as error (see the interpretation note), so the
  headline 0.6942 overstates pure character error by an amount
  this study diagnoses on one document but does not quantify
  across the set.
- 300: one corpus, one vision model, one pass per document.
  Arm B has no repeat runs, so its run-to-run variance is
  unmeasured.
- 200: the Arm B client was corrected mid-run (D2). Failure
  semantics were unchanged and the incident is documented, but
  a stricter protocol would have restarted the arm from zero
  under the corrected client.

What the grade credits: a genuinely locked pre-registration
with decidable pass lines; both arms executed in full on the
published test split; a politically inconvenient failure mode
(the sponsor route's own rate limit) measured, counted, and
published rather than routed around; verdicts and every
headline number generated by script from raw records; and a
claim that survived a Jev review route by hand-verification
against those records.
