# Amendment A2 report: Arm A re-run and WER decomposition

Post-registration diagnostic registered in DECISIONS.md (Amendment A2, 2026-11-17). Arm A re-ran on all 50 FUNSD test documents with the frozen harness unchanged; the OCR token sequence of every document is saved in results/amendment_a2_arm_a.jsonl. Arm B was not touched and no API calls were made. No frozen verdict changes.

## Arm A re-run vs the committed record (frozen scorer)

| Figure | Committed | Re-run | Match |
| --- | --- | --- | --- |
| True positives | 40 | 40 | yes |
| Predicted pairs | 425 | 425 | yes |
| Ground-truth pairs | 816 | 816 | yes |
| Precision (micro) | 0.0941 | 0.0941 | yes |
| Recall (micro) | 0.0490 | 0.0490 | yes |
| F1 (micro) | 0.0645 | 0.0645 | yes |
| WER (micro) | 0.6942 | 0.6942 | yes |
| WER edits | 6060 | 6060 | yes |
| Reference tokens | 8729 | 8729 | yes |

Per-document comparison: all 50 documents match the committed rows of results/metrics.json and results/arm_a.jsonl on predicted pairs (exact pair lists included), true positives, F1, WER, WER edits, reference tokens, and OCR word count. Seconds differ (timing is not compared).

## WER decomposition (micro, 50 documents)

Frozen WER: 6060 edits over 8729 reference tokens = 0.6942. Method (Amendment A2): E0 is the frozen token Levenshtein; E_S recomputes it after sorting both sequences (removes reading order); E_SN recomputes it after sorting and the tokenization normalization C (split tokens into maximal alphanumeric runs, drop pieces with no alphanumeric character). Shares use the frozen denominator, so they sum to the frozen WER.

| Component | Edits | Share of frozen WER | WER points |
| --- | --- | --- | --- |
| Reading-order divergence (E0 - E_S) | 873 | 14.4% | 0.1000 |
| Tokenization divergence (E_S - E_SN) | 1240 | 20.5% | 0.1421 |
| Residual token error (E_SN) | 3947 | 65.1% | 0.4522 |
| Total (frozen WER) | 6060 | 100.0% | 0.6942 |

Method note: the decomposition is a micro-level decomposition (edit counts summed over the 50 documents before shares are taken). Per document the order step is not guaranteed monotonic, because Levenshtein distance on sorted sequences is a different alignment, not a bounded relaxation: in 6 of 50 documents sorting raised the count slightly (82092117 +5, 82562350 +2, 83635935 +3, 83823750 +4, 87125460 +4, 87428306 +4; +22 edits in total across those documents), more than offset by the other 44 documents. The tokenization step raised no document's count (0 documents). The micro totals above are monotonic: 6060 > 5187 > 3947.

The residual 0.4522 is the token error rate that survives removing order and tokenization divergence: tokens whose alphanumeric content itself differs (OCR character misreads surfacing as whole-token mismatches, plus tokens missed or invented outright). It is an upper bound on pure character error read at token granularity, not a character-level error rate.

Descriptive cross-checks (not part of the decomposition): raw token multiset overlap is 4334 of 8729 reference tokens (0.4965); after normalization C it is 5451 of 8726 canonical reference tokens (0.6247). On document 82092117, the one-document diagnostic of record, the raw overlap is 133 of 223 reference tokens, and its counts are E0 108, E_S 113, E_SN 67.

## Per-document decomposition

| Document | Ref tokens | E0 | E_S | E_SN | WER | Residual WER |
| --- | --- | --- | --- | --- | --- | --- |
| 82092117 | 223 | 108 | 113 | 67 | 0.4843 | 0.3004 |
| 82200067_0069 | 167 | 130 | 112 | 92 | 0.7784 | 0.5509 |
| 82250337_0338 | 214 | 94 | 85 | 56 | 0.4393 | 0.2617 |
| 82251504 | 222 | 196 | 180 | 165 | 0.8829 | 0.7432 |
| 82252956_2958 | 113 | 67 | 51 | 39 | 0.5929 | 0.3451 |
| 82253058_3059 | 187 | 106 | 90 | 63 | 0.5668 | 0.3369 |
| 82253245_3247 | 234 | 146 | 144 | 92 | 0.6239 | 0.3932 |
| 82253362_3364 | 228 | 195 | 177 | 152 | 0.8553 | 0.6667 |
| 82254765 | 116 | 86 | 72 | 55 | 0.7414 | 0.4741 |
| 82491256 | 71 | 68 | 32 | 12 | 0.9577 | 0.1690 |
| 82504862 | 63 | 57 | 36 | 13 | 0.9048 | 0.2063 |
| 82562350 | 192 | 140 | 142 | 131 | 0.7292 | 0.6823 |
| 82573104 | 135 | 69 | 62 | 39 | 0.5111 | 0.2889 |
| 82837252 | 112 | 83 | 71 | 64 | 0.7411 | 0.5714 |
| 83443897 | 195 | 108 | 96 | 66 | 0.5538 | 0.3385 |
| 83553333_3334 | 204 | 165 | 144 | 102 | 0.8088 | 0.5000 |
| 83573282 | 299 | 237 | 200 | 151 | 0.7926 | 0.5050 |
| 83594639 | 87 | 77 | 61 | 60 | 0.8851 | 0.6897 |
| 83624198 | 190 | 107 | 102 | 78 | 0.5632 | 0.4105 |
| 83635935 | 141 | 119 | 122 | 117 | 0.8440 | 0.8298 |
| 83641919_1921 | 209 | 185 | 164 | 151 | 0.8852 | 0.7225 |
| 83772145 | 236 | 182 | 165 | 133 | 0.7712 | 0.5636 |
| 83823750 | 163 | 125 | 129 | 110 | 0.7669 | 0.6748 |
| 83996357 | 98 | 86 | 58 | 37 | 0.8776 | 0.3776 |
| 85201976 | 80 | 43 | 30 | 21 | 0.5375 | 0.2625 |
| 85240939 | 154 | 83 | 83 | 65 | 0.5390 | 0.4221 |
| 85540866 | 25 | 17 | 5 | 2 | 0.6800 | 0.0800 |
| 85629964 | 94 | 71 | 60 | 17 | 0.7553 | 0.1809 |
| 86075409_5410 | 125 | 111 | 94 | 71 | 0.8880 | 0.5680 |
| 86079776_9777 | 210 | 153 | 124 | 111 | 0.7286 | 0.5286 |
| 86220490 | 75 | 35 | 30 | 19 | 0.4667 | 0.2533 |
| 86230203_0206 | 137 | 137 | 98 | 85 | 1.0000 | 0.6204 |
| 86236474_6476 | 118 | 33 | 27 | 5 | 0.2797 | 0.0424 |
| 86244113 | 80 | 34 | 25 | 11 | 0.4250 | 0.1375 |
| 86263525 | 90 | 41 | 32 | 12 | 0.4556 | 0.1333 |
| 86328049_8050 | 199 | 170 | 154 | 92 | 0.8543 | 0.4623 |
| 87086073 | 56 | 42 | 39 | 35 | 0.7500 | 0.6250 |
| 87093315_87093318 | 194 | 165 | 121 | 90 | 0.8505 | 0.4639 |
| 87125460 | 72 | 27 | 31 | 27 | 0.3750 | 0.3750 |
| 87137840 | 76 | 61 | 59 | 49 | 0.8026 | 0.6447 |
| 87147607 | 204 | 126 | 123 | 108 | 0.6176 | 0.5294 |
| 87332450 | 160 | 90 | 68 | 43 | 0.5625 | 0.2687 |
| 87428306 | 187 | 87 | 91 | 62 | 0.4652 | 0.3316 |
| 87528321 | 198 | 139 | 96 | 67 | 0.7020 | 0.3384 |
| 87528380 | 411 | 349 | 286 | 222 | 0.8491 | 0.5401 |
| 87594142_87594144 | 437 | 272 | 242 | 191 | 0.6224 | 0.4371 |
| 89856243 | 311 | 157 | 123 | 87 | 0.5048 | 0.2797 |
| 91814768_91814769 | 356 | 257 | 166 | 116 | 0.7219 | 0.3258 |
| 92380595 | 270 | 227 | 182 | 143 | 0.8407 | 0.5296 |
| 93106788 | 311 | 197 | 190 | 151 | 0.6334 | 0.4855 |

Full machine-readable results: results/amendment_a2_wer_decomposition.json; per-document re-run records with token sequences: results/amendment_a2_arm_a.jsonl; generator: scripts/amendment_a2_diagnostic.py.
