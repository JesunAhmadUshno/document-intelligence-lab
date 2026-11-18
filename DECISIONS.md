# Decisions and amendments

## D1: Tesseract runs from a user-space install

This VM has no system Tesseract and no sudo. Rather than
substituting a different OCR engine, Tesseract 5.3.4 (the Ubuntu
tesseract-ocr package, with tesseract-ocr-eng 4.1.0 language data)
is installed in user space: packages fetched with a user-space
apt state directory and unpacked with dpkg -x under
.tools/tesseract-root, launched through scripts/tesseract.sh with
LD_LIBRARY_PATH and TESSDATA_PREFIX set. Arm A is therefore the
real Tesseract the pre-registration names, not a substitute
engine. scripts/setup_tesseract.sh reproduces the install. The
version string is recorded in results/run_manifest.json.

## D3: the credential-helper import is optional at module load

After the results commit, CI failed on both Python versions:
arm_b.py imported the connector's dynamic-credentials helper at
module load, and that helper exists only on the machine hosting
the connected route, so the test module could not import on a
clean runner. The import is now guarded; the helper is required
only when a call is actually made, and parsing and scoring
import anywhere. No measured behavior changed: the run path on
the machine of record is identical, and this fix landed after
every run record was written.

## D2: Arm B calls carry a hard deadline in the client

During the full run, one document's Gemini call sat in flight
far beyond the intended 180-second timeout: a urllib socket
timeout does not bound a slow-drip response. The client now runs
each attempt on a daemon thread with a hard 180-second join
deadline; exceeding it raises a timeout, which the frozen failure
rule already covers (one retry, then the document is failed and
counted). This is a harness correction, not a protocol change:
the pre-registration freezes the failure semantics, and the
client now actually enforces them. The stuck attempt produced no
record and no number; the document was re-run under the fixed
client.

## Amendment A1 to PREREGISTRATION.md (before any measured run)

R2's value search, as originally written, continues past an
intervening key line and can assign that key's value to an
earlier key (example: lines "NAME:", "FAX:", "555-1234" would
pair NAME with the number and leave FAX valueless). That is a
defect in the rule text, found by a unit test before any run.
Amended rule: the value search scans later lines in order and
stops at the first line that qualifies as a key under R1 or R2;
only non-key lines before that boundary are candidates. No
measured run precedes this amendment; every run in this repository uses the amended rule.

## Amendment A2: WER decomposition diagnostic (post-registration, 2026-11-17)

AUDIT.md deducts 500 because the frozen WER of 0.6942 counts
reading-order and tokenization divergence as error, overstating
pure character error by an amount the study diagnosed on one
document (82092117) but never quantified across the 50-document
test set. Arm A's per-document WER edit counts also rest on run
records because the OCR token sequences were never committed.
This amendment registers a post-registration diagnostic that
closes both gaps. It changes no frozen verdict, no frozen
metric, and no committed record; Arm B is not touched and no
API calls are made.

(a) Arm A re-run. Arm A (Tesseract 5.3.4 via the D1 user-space
install, plus the frozen rules R1 to R3 with Amendment A1) is
re-run on all 50 test documents with the existing harness code
(src/arm_a.py, src/common.py) unchanged. This time the OCR
hypothesis token sequence of every document is saved, in a new
file (results/amendment_a2_arm_a.jsonl), alongside the pairs,
seconds, OCR word count, WER edits, and reference token count,
so the WER edit counts become recomputable from committed
records. The re-run is first scored with the frozen scorer and
compared figure by figure against the committed record
(P 0.0941, R 0.0490, F1 0.0645, WER 0.6942 as 6,060 edits over
8,729 reference tokens, and the per-document rows of
results/metrics.json) before any decomposition is presented.

(b) WER decomposition, deterministic method. For each document,
with R the frozen reference token sequence and H the frozen
hypothesis token sequence (both as src/common.py defines them),
compute three token-Levenshtein edit counts with the existing
src/common.py levenshtein function:

- E0: Lev(R, H), the frozen count.
- E_S: Lev(sort(R), sort(H)), both sequences sorted
  lexicographically (Python string order). Sorting removes
  reading order while keeping both token multisets intact.
- E_SN: Lev(sort(C(R)), sort(C(H))), where C is the following
  tokenization normalization, applied token by token to both
  sequences: split each token into its maximal runs of
  alphanumeric characters (Unicode letters or digits) and
  discard every piece that contains no alphanumeric character.
  Example: "(614)" becomes "614"; "466-" and "-466" both become
  "466"; a hypothesis token "466-5087" becomes "466", "5087";
  "09/" becomes "09"; "100's" becomes "100", "s"; a token that
  is pure punctuation (for example "&" or a checkbox glyph)
  contributes no piece. C therefore removes exactly the
  divergence between FUNSD annotation tokenization (numbers
  and punctuation split or attached inconsistently) and
  Tesseract tokenization, and nothing else.

Counts are summed over the 50 documents (micro), and every
share uses the frozen denominator of 8,729 reference tokens,
so the three shares sum to the frozen WER:

- reading-order share: (E0 - E_S) / 8,729
- tokenization share: (E_S - E_SN) / 8,729
- residual share: E_SN / 8,729, the token edits that survive
  removing order and tokenization divergence: tokens whose
  alphanumeric content itself differs (OCR character misreads
  surfacing as whole-token mismatches, plus tokens missed or
  invented outright).

Per-document E0, E_S, and E_SN are reported alongside the
micro totals. As a descriptive cross-check only, the
multiset overlap of the tokenization-normalized sequences
(common tokens over reference tokens, micro and for document
82092117) is also reported; it is not part of the
decomposition. Outputs go to new files only:
results/amendment_a2_arm_a.jsonl,
results/amendment_a2_wer_decomposition.json, and
results/amendment_a2_report.md. RESULTS.md, results/metrics.json,
results/arm_a.jsonl, and results/arm_b.jsonl are not modified.

## Amendment A3: Arm B paced completion (post-registration, 2026-11-17)

The frozen Arm B run answered 21 of the 50 test documents. The
other 29 are recorded in results/arm_b.jsonl as failed documents
with zero predicted pairs: 27 with HTTP 429 (Too Many Requests)
on both attempts and 2 with a timeout on the 180-second deadline
(82200067_0069, 86075409_5410), verified document by document
from the committed file on 2026-11-17. The H1 comparison in
RESULTS.md is therefore rate-limit-bound: Arm B's frozen F1 of
0.4029 prices 29 quota and timeout failures as zero-pair
documents. Jesun approved a paced completion on 2026-11-17
(default ruling 7). This amendment registers that completion. It
changes no frozen verdict, no frozen metric, and no committed
record: RESULTS.md, results/metrics.json, and
results/arm_b.jsonl are not modified, and the frozen verdicts
are not recomputed by this run alone.

(a) Scope. Arm B is run again, through src/arm_b.py unchanged
(the same route, the same model gemini-3-flash-preview, the
same frozen prompt, temperature 0, and the same within-document
failure rule of one retry after 5 seconds), for exactly the 29
documents whose frozen record is failed:

82200067_0069, 82837252, 83443897, 83553333_3334, 83594639,
83624198, 83635935, 83641919_1921, 83772145, 83996357,
85201976, 85240939, 85540866, 85629964, 86075409_5410,
86220490, 86230203_0206, 86328049_8050, 87093315_87093318,
87125460, 87147607, 87332450, 87528321, 87528380,
87594142_87594144, 89856243, 91814768_91814769, 92380595,
93106788.

The 21 documents the frozen run answered are not re-run.

(b) Pacing rule. Successive documents are separated by a pause
of at least 5 seconds in the driver, on top of the frozen
5-second pause before the within-document retry, so at least 5
seconds elapse between API requests. The driver is
scripts/amendment_a3_completion.py.

(c) Stop rule. If five consecutive documents in this completion
run end in an HTTP 429 failure (the recorded failure granularity
of src/arm_b.py), the run stops there and reports the partial
count exactly; the remaining documents are not attempted. Any
other outcome (an answer, a timeout, a parse failure, another
error) resets the consecutive count.

(d) Output. Records go to a new file only,
results/amendment_arm_b_completion.jsonl, one JSONL record per
attempted document in the same shape as results/arm_b.jsonl,
appending and flushing so an interrupted run loses nothing;
documents already present in the new file are skipped on a
later invocation (resume). The frozen results/arm_b.jsonl is
never appended to.

(e) Scoring under this amendment. The completed documents are
scored with the frozen scorer (src/common.py match_pairs and
prf, the functions scripts/make_results.py uses) against the
ground truth, and set beside the committed Arm A records for
the same documents and beside the frozen figures for the 21
documents the original run answered. The scoring output goes
to new files only: results/amendment_a3_scoring.json and
results/amendment_a3_report.md. A full-50 Arm B comparison
still needs a separate rescoring record that merges the
completion records with the frozen ones and recomputes the
headline numbers under its own amendment; nothing in this
amendment does that.

## Amendment A4: full-50 Arm B rescoring (post-registration, 2026-11-17)

Amendment A3 completed 22 of the 29 documents the frozen Arm B
run failed, but by its own terms it did not recompute the
full-50 headline numbers or the H1 and H3 verdicts. This
amendment registers that rescoring. It changes no frozen
verdict, no frozen metric, and no committed record on disk:
RESULTS.md, results/metrics.json, results/arm_a.jsonl, and
results/arm_b.jsonl are not modified.

(a) Merge rule. The merged Arm B record set is the frozen
results/arm_b.jsonl with every record whose frozen entry is
failed replaced by the corresponding record in
results/amendment_arm_b_completion.jsonl. The 21 documents the
frozen run answered keep their frozen records untouched. The
7 documents the completion still did not answer (82200067_0069,
83996357, 87147607, 87594142_87594144, 89856243, 92380595,
93106788) keep a failed record with zero predicted pairs, so
they are counted, never dropped, exactly as the frozen failure
rule requires.

(b) Computation. The headline Arm B numbers over all 50
documents, and the H1 and H3 verdicts under the frozen pass
lines, are recomputed with scripts/make_results.py's own logic
(its compute and verdicts functions), fed the merged record
set; Arm A is fed from the frozen results/arm_a.jsonl
unchanged, so its figures and the H2 verdict carry over
exactly. The merged timing spread (median, mean, IQR of the
merged Arm B seconds) is computed by the same code, which the
subset arithmetic of Amendment A3 could not supply. Before
any merged figure is produced, the same computation run on
the frozen inputs must reproduce results/metrics.json
exactly; if it does not, the rescoring stops and writes
nothing.

(c) Output. The rescoring record goes to new files only:
results/amendment_rescoring.json and
results/amendment_rescoring_report.md, produced by
scripts/amendment_rescoring.py. The report states which
frozen headline numbers and verdicts the merged record
supersedes for a future paper version, while the frozen
RESULTS.md itself stays untouched on disk as the record of
the original run.
