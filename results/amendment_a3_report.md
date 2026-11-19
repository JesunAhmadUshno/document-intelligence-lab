# Amendment A3: Arm B paced completion, scoring

Registered in DECISIONS.md as Amendment A3 (2026-11-17).
Scored with the frozen scorer (src/common.py), verified
against results/metrics.json for all 50 documents before
any subset figure was computed. Frozen verdicts are not
recomputed here.

## Outcome

- Missing documents in the frozen run: 29 (27 HTTP 429, 2 timeouts).
- Attempted in this completion: 29.
- Answered now: 22.
- Still failed: 7: 82200067_0069, 83996357, 87147607, 87594142_87594144, 89856243, 92380595, 93106788.
- Not attempted (stop rule): 0.

## Figures

- Frozen run, the 21 documents it answered, Arm B: P 0.7865, R 0.7517, F1 0.7687 (TP 221 / pred 281 / GT 294).
- Completion, the 22 documents answered now, Arm B: P 0.7458, R 0.6899, F1 0.7168 (TP 267 / pred 358 / GT 387).
- Same 22 documents, committed Arm A: P 0.1262, R 0.0672, F1 0.0877 (TP 26 / pred 206 / GT 387).
- All 29 missing documents (completion failures counted as zero pairs), Arm B: P 0.7458, R 0.5115, F1 0.6068 (TP 267 / pred 358 / GT 522).
- All 29 missing documents, committed Arm A: P 0.0952, R 0.0498, F1 0.0654 (TP 26 / pred 273 / GT 522).

## Per-document (documents answered in this completion)

| Document | GT | B pred | B TP | B F1 | B s | A pred | A TP | A F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 82837252 | 9 | 6 | 6 | 0.800 | 11.49 | 12 | 1 | 0.095 |
| 83443897 | 12 | 11 | 10 | 0.870 | 7.82 | 10 | 5 | 0.455 |
| 83553333_3334 | 31 | 27 | 25 | 0.862 | 15.64 | 13 | 0 | 0.000 |
| 83594639 | 6 | 6 | 6 | 1.000 | 5.51 | 6 | 4 | 0.667 |
| 83624198 | 12 | 10 | 9 | 0.818 | 7.23 | 11 | 6 | 0.522 |
| 83635935 | 4 | 4 | 3 | 0.750 | 4.25 | 5 | 0 | 0.000 |
| 83641919_1921 | 56 | 61 | 51 | 0.872 | 36.90 | 7 | 2 | 0.063 |
| 83772145 | 10 | 8 | 6 | 0.667 | 8.90 | 13 | 0 | 0.000 |
| 85201976 | 0 | 0 | 0 | 0.000 | 10.00 | 3 | 0 | 0.000 |
| 85240939 | 10 | 8 | 7 | 0.778 | 34.37 | 9 | 1 | 0.105 |
| 85540866 | 0 | 0 | 0 | 0.000 | 7.31 | 2 | 0 | 0.000 |
| 85629964 | 0 | 0 | 0 | 0.000 | 6.66 | 13 | 0 | 0.000 |
| 86075409_5410 | 15 | 16 | 9 | 0.581 | 233.88 | 16 | 2 | 0.129 |
| 86220490 | 8 | 8 | 8 | 1.000 | 6.30 | 1 | 0 | 0.000 |
| 86230203_0206 | 32 | 35 | 26 | 0.776 | 25.77 | 16 | 0 | 0.000 |
| 86328049_8050 | 38 | 36 | 19 | 0.514 | 119.40 | 2 | 0 | 0.000 |
| 87093315_87093318 | 54 | 43 | 33 | 0.680 | 43.41 | 10 | 0 | 0.000 |
| 87125460 | 11 | 9 | 9 | 0.900 | 34.93 | 1 | 0 | 0.000 |
| 87332450 | 6 | 0 | 0 | 0.000 | 24.97 | 12 | 1 | 0.111 |
| 87528321 | 16 | 18 | 12 | 0.706 | 37.68 | 12 | 0 | 0.000 |
| 87528380 | 29 | 28 | 16 | 0.561 | 130.26 | 21 | 4 | 0.160 |
| 91814768_91814769 | 28 | 24 | 12 | 0.462 | 78.85 | 11 | 0 | 0.000 |

## What the full-50 comparison needs next

A separate rescoring record, under its own amendment,
that merges the completion records in
results/amendment_arm_b_completion.jsonl with the frozen
records in results/arm_b.jsonl (completion records
replacing the failed frozen ones) and recomputes the
headline Arm B numbers and the H1/H3 verdicts with
scripts/make_results.py's logic, writing to new files
only. Until that record exists, the frozen headline
numbers in RESULTS.md stand as the study's record.
