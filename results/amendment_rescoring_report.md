# Amendment A4: full-50 Arm B rescoring

Registered in DECISIONS.md as Amendment A4 (2026-11-17).
Computed by scripts/amendment_rescoring.py with
scripts/make_results.py's own compute and verdicts logic,
after that logic reproduced results/metrics.json exactly
from the frozen inputs. The merged Arm B set is the frozen
results/arm_b.jsonl with the 29 failed records replaced by
results/amendment_arm_b_completion.jsonl (Amendment A3);
the 7 documents still unanswered keep failed records with
zero predicted pairs. Arm A is the frozen record, unchanged.

## Merged headline numbers (all 50 documents)

| Measure | Arm A: Tesseract + rules | Arm B: Gemini vision (merged) |
| --- | --- | --- |
| Field precision (micro) | 0.0941 | 0.7637 |
| Field recall (micro) | 0.0490 | 0.5980 |
| Field F1 (micro) | 0.0645 | 0.6708 |
| True positives / predicted / ground truth | 40 / 425 / 816 | 488 / 639 / 816 |
| Median seconds per document | 3.583 | 24.146 |
| Mean seconds per document | 4.099 | 60.320 |
| Time IQR (seconds) | 3.471 | 33.355 |

Arm B merged: 71 API calls for 50 documents; 7 failed documents (counted, with zero predicted pairs, never dropped): 82200067_0069, 83996357, 87147607, 87594142_87594144, 89856243, 92380595, 93106788.

Arm A figures are identical to the frozen record (P 0.0941, R 0.0490, F1 0.0645, WER 0.6942), so H2 stands as frozen: **CONFIRMED**.

## Verdicts under the frozen pass lines

- H1 (vision-LLM beats classical on field F1 by at least 0.15): **CONFIRMED**. Merged F1 difference is 0.6063 (frozen: 0.3385, verdict CONFIRMED).
- H3 (classical arm at least 5 times faster per document): **CONFIRMED**. Merged median times: Arm A 3.583 s, Arm B 24.146 s (ratio 6.74; merged Arm B mean 60.320 s, IQR 33.355 s). Frozen: Arm B median 7.462 s, verdict INCONCLUSIVE.

## What this record supersedes

For a future paper version, this merged record supersedes
the frozen Arm B headline numbers (P 0.7865, R 0.2708, F1 0.4029;
29 failed documents) and the frozen H1 and H3 verdicts
wherever they differ above. The frozen RESULTS.md and
results/metrics.json stay untouched on disk as the record
of the original run; nothing in this amendment rewrites
them.
