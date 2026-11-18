"""Amendment A2 diagnostic (DECISIONS.md, 2026-11-17).

Re-runs Arm A on all 50 FUNSD test documents with the frozen
harness code unchanged, saves the OCR hypothesis token sequence
of every document (which the original run did not commit),
scores the re-run with the frozen scorer, compares it figure by
figure against the committed record, and decomposes the frozen
WER into reading-order, tokenization, and residual shares by
the deterministic method registered in Amendment A2.

Outputs (new files only):
  results/amendment_a2_arm_a.jsonl
  results/amendment_a2_wer_decomposition.json
  results/amendment_a2_report.md

Arm B is not touched; no API calls are made; no committed file
is modified.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import arm_a  # noqa: E402
import common  # noqa: E402

DATA_DIR = ROOT / "data"
RESULTS = ROOT / "results"
TESSERACT = str(ROOT / "scripts" / "tesseract.sh")


def canon_pieces(token):
    """Amendment A2 normalization C: maximal alphanumeric runs
    of a token; pieces with no alphanumeric character dropped."""
    pieces = []
    current = []
    for ch in token:
        if ch.isalnum():
            current.append(ch)
        elif current:
            pieces.append("".join(current))
            current = []
    if current:
        pieces.append("".join(current))
    return pieces


def canon_seq(tokens):
    out = []
    for tok in tokens:
        out.extend(canon_pieces(tok))
    return out


def fmt(x, nd=4):
    return ("%.*f" % (nd, x))


def main():
    doc_ids = common.test_doc_ids(str(DATA_DIR))
    assert len(doc_ids) == 50, len(doc_ids)

    committed_metrics = json.loads(
        (RESULTS / "metrics.json").read_text(encoding="utf-8"))
    committed_rows = {r["doc"]: r for r in committed_metrics["rows"]}
    committed_arm_a = {}
    for line in open(RESULTS / "arm_a.jsonl", encoding="utf-8"):
        line = line.strip()
        if line:
            rec = json.loads(line)
            committed_arm_a[rec["doc"]] = rec

    records = []
    tot_tp = tot_pred = tot_truth = 0
    sum_e0 = sum_es = sum_esn = 0
    sum_ref = 0
    sum_overlap_raw = sum_overlap_canon = 0
    sum_ref_canon = 0
    per_doc = []
    mismatches = []

    out_jsonl = RESULTS / "amendment_a2_arm_a.jsonl"
    # Resume support: records already in the output file (from an
    # interrupted run of this same script) are reused verbatim;
    # their pairs and token sequences are deterministic OCR
    # outputs, and scoring and decomposition are recomputed from
    # them below exactly as for a fresh record.
    saved = {}
    if out_jsonl.exists():
        for line in open(out_jsonl, encoding="utf-8"):
            line = line.strip()
            if line:
                rec_saved = json.loads(line)
                saved[rec_saved["doc"]] = rec_saved
    with open(out_jsonl, "a", encoding="utf-8") as fh:
        for doc_id in doc_ids:
            ann = common.load_annotation(
                common.annotation_path(str(DATA_DIR), doc_id))
            gt_pairs = common.ground_truth_pairs(ann)
            ref = common.reference_tokens(ann)
            if doc_id in saved:
                rec = {
                    "pairs": saved[doc_id]["pairs"],
                    "seconds": saved[doc_id]["seconds"],
                    "ocr_words": saved[doc_id]["ocr_words"],
                    "hyp_tokens": saved[doc_id]["hyp_tokens"],
                }
            else:
                rec = arm_a.run_document(
                    common.image_path(str(DATA_DIR), doc_id), TESSERACT)
            hyp = rec["hyp_tokens"]
            pairs = [tuple(p) for p in rec["pairs"]]
            tp, npred, ntruth = common.match_pairs(pairs, gt_pairs)
            edits, ref_n = common.wer_counts(ref, hyp)

            record = {
                "doc": doc_id,
                "pairs": rec["pairs"],
                "seconds": rec["seconds"],
                "ocr_words": rec["ocr_words"],
                "wer_edits": edits,
                "ref_tokens": ref_n,
                "hyp_tokens": hyp,
            }
            if doc_id not in saved:
                fh.write(json.dumps(record) + "\n")
                fh.flush()
            records.append(record)

            # Decomposition (Amendment A2 method).
            e0 = edits
            es = common.levenshtein(sorted(ref), sorted(hyp))
            ref_c = canon_seq(ref)
            hyp_c = canon_seq(hyp)
            esn = common.levenshtein(sorted(ref_c), sorted(hyp_c))
            overlap_raw = sum((Counter(ref) & Counter(hyp)).values())
            overlap_canon = sum(
                (Counter(ref_c) & Counter(hyp_c)).values())

            tot_tp += tp
            tot_pred += npred
            tot_truth += ntruth
            sum_e0 += e0
            sum_es += es
            sum_esn += esn
            sum_ref += ref_n
            sum_overlap_raw += overlap_raw
            sum_overlap_canon += overlap_canon
            sum_ref_canon += len(ref_c)

            p_doc, r_doc, f1_doc = common.prf(tp, npred, ntruth)
            row = {
                "doc": doc_id,
                "ref_tokens": ref_n,
                "hyp_tokens": len(hyp),
                "ref_tokens_canon": len(ref_c),
                "hyp_tokens_canon": len(hyp_c),
                "tp": tp,
                "pred": npred,
                "truth": ntruth,
                "precision": p_doc,
                "recall": r_doc,
                "f1": f1_doc,
                "wer": edits / ref_n if ref_n else 0.0,
                "e0": e0,
                "e_sorted": es,
                "e_sorted_canon": esn,
                "overlap_raw": overlap_raw,
                "overlap_canon": overlap_canon,
                "seconds": rec["seconds"],
            }
            per_doc.append(row)

            # Comparison against the committed record.
            cm = committed_rows[doc_id]
            ca = committed_arm_a[doc_id]
            checks = [
                ("a_pred", npred, cm["a_pred"]),
                ("a_tp", tp, cm["a_tp"]),
                ("a_f1", round(f1_doc, 10), round(cm["a_f1"], 10)),
                ("a_wer", round(edits / ref_n, 10) if ref_n else 0.0,
                 round(cm["a_wer"], 10)),
                ("wer_edits", edits, ca["wer_edits"]),
                ("ref_tokens", ref_n, ca["ref_tokens"]),
                ("ocr_words", rec["ocr_words"], ca["ocr_words"]),
                ("pairs_exact", rec["pairs"] == ca["pairs"], True),
            ]
            for name, got, want in checks:
                if got != want:
                    mismatches.append({
                        "doc": doc_id, "field": name,
                        "rerun": got, "committed": want})
            print("A2", doc_id, "pred", npred, "tp", tp,
                  "e0", e0, "eS", es, "eSN", esn, flush=True)

    precision, recall, f1 = common.prf(tot_tp, tot_pred, tot_truth)
    wer = sum_e0 / sum_ref if sum_ref else 0.0
    denom = sum_ref
    decomp = {
        "e0": sum_e0,
        "e_sorted": sum_es,
        "e_sorted_canon": sum_esn,
        "denominator_ref_tokens": denom,
        "wer_frozen": sum_e0 / denom,
        "wer_after_order_removed": sum_es / denom,
        "wer_residual": sum_esn / denom,
        "reading_order_edits": sum_e0 - sum_es,
        "tokenization_edits": sum_es - sum_esn,
        "residual_edits": sum_esn,
        "reading_order_share_of_wer": (sum_e0 - sum_es) / sum_e0,
        "tokenization_share_of_wer": (sum_es - sum_esn) / sum_e0,
        "residual_share_of_wer": sum_esn / sum_e0,
        "reading_order_share_points": (sum_e0 - sum_es) / denom,
        "tokenization_share_points": (sum_es - sum_esn) / denom,
        "residual_share_points": sum_esn / denom,
        "overlap_raw_micro": sum_overlap_raw / sum_ref,
        "overlap_raw_tokens": sum_overlap_raw,
        "overlap_canon_micro": sum_overlap_canon / sum_ref_canon,
        "overlap_canon_tokens": sum_overlap_canon,
        "ref_tokens_canon_total": sum_ref_canon,
    }
    comparison = {
        "rerun": {
            "tp": tot_tp, "predicted": tot_pred, "truth": tot_truth,
            "precision": precision, "recall": recall, "f1": f1,
            "wer": wer, "wer_edits": sum_e0, "ref_tokens": sum_ref,
        },
        "committed": {
            "tp": committed_metrics["arm_a"]["tp"],
            "predicted": committed_metrics["arm_a"]["predicted"],
            "truth": committed_metrics["arm_a"]["truth"],
            "precision": committed_metrics["arm_a"]["precision"],
            "recall": committed_metrics["arm_a"]["recall"],
            "f1": committed_metrics["arm_a"]["f1"],
            "wer": committed_metrics["arm_a"]["wer"],
            "wer_edits": committed_metrics["arm_a"]["wer_edits"],
            "ref_tokens": committed_metrics["arm_a"]["ref_tokens"],
        },
        "per_document_mismatches": mismatches,
    }
    diag_82092117 = next(r for r in per_doc if r["doc"] == "82092117")

    payload = {
        "amendment": "A2 (DECISIONS.md, 2026-11-17)",
        "method": {
            "e0": "Lev(R, H) frozen token sequences (src/common.py)",
            "e_sorted": "Lev(sort(R), sort(H)) lexicographic",
            "e_sorted_canon": "Lev(sort(C(R)), sort(C(H))); C splits "
                              "each token into maximal alphanumeric "
                              "runs and drops pieces with no "
                              "alphanumeric character",
            "shares": "micro over 50 documents, denominator is the "
                      "frozen reference token total",
        },
        "comparison": comparison,
        "decomposition": decomp,
        "diagnostic_doc_82092117": {
            "ref_tokens": diag_82092117["ref_tokens"],
            "overlap_raw": diag_82092117["overlap_raw"],
            "overlap_canon": diag_82092117["overlap_canon"],
            "e0": diag_82092117["e0"],
            "e_sorted": diag_82092117["e_sorted"],
            "e_sorted_canon": diag_82092117["e_sorted_canon"],
        },
        "per_document": per_doc,
    }
    (RESULTS / "amendment_a2_wer_decomposition.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Markdown report, generated from the same numbers.
    c = comparison["committed"]
    r = comparison["rerun"]
    lines = []
    lines.append("# Amendment A2 report: Arm A re-run and WER decomposition")
    lines.append("")
    lines.append("Post-registration diagnostic registered in DECISIONS.md "
                 "(Amendment A2, 2026-11-17). Arm A re-ran on all 50 "
                 "FUNSD test documents with the frozen harness unchanged; "
                 "the OCR token sequence of every document is saved in "
                 "results/amendment_a2_arm_a.jsonl. Arm B was not touched "
                 "and no API calls were made. No frozen verdict changes.")
    lines.append("")
    lines.append("## Arm A re-run vs the committed record (frozen scorer)")
    lines.append("")
    lines.append("| Figure | Committed | Re-run | Match |")
    lines.append("| --- | --- | --- | --- |")
    for label, ck, rk, nd in [
            ("True positives", "tp", "tp", 0),
            ("Predicted pairs", "predicted", "predicted", 0),
            ("Ground-truth pairs", "truth", "truth", 0),
            ("Precision (micro)", "precision", "precision", 4),
            ("Recall (micro)", "recall", "recall", 4),
            ("F1 (micro)", "f1", "f1", 4),
            ("WER (micro)", "wer", "wer", 4),
            ("WER edits", "wer_edits", "wer_edits", 0),
            ("Reference tokens", "ref_tokens", "ref_tokens", 0)]:
        cv, rv = c[ck], r[rk]
        match = "yes" if (round(cv, 10) == round(rv, 10)) else "NO"
        lines.append("| %s | %s | %s | %s |" % (
            label, fmt(cv, nd) if nd else cv,
            fmt(rv, nd) if nd else rv, match))
    lines.append("")
    if mismatches:
        lines.append("Per-document mismatches against results/metrics.json "
                     "and results/arm_a.jsonl (%d):" % len(mismatches))
        lines.append("")
        for m in mismatches:
            lines.append("- %s, %s: re-run %s, committed %s" % (
                m["doc"], m["field"], m["rerun"], m["committed"]))
        lines.append("")
    else:
        lines.append("Per-document comparison: all 50 documents match the "
                     "committed rows of results/metrics.json and "
                     "results/arm_a.jsonl on predicted pairs (exact pair "
                     "lists included), true positives, F1, WER, WER edits, "
                     "reference tokens, and OCR word count. Seconds differ "
                     "(timing is not compared).")
        lines.append("")
    lines.append("## WER decomposition (micro, 50 documents)")
    lines.append("")
    lines.append("Frozen WER: %d edits over %d reference tokens = %s. "
                 "Method (Amendment A2): E0 is the frozen token "
                 "Levenshtein; E_S recomputes it after sorting both "
                 "sequences (removes reading order); E_SN recomputes it "
                 "after sorting and the tokenization normalization C "
                 "(split tokens into maximal alphanumeric runs, drop "
                 "pieces with no alphanumeric character). Shares use the "
                 "frozen denominator, so they sum to the frozen WER."
                 % (sum_e0, denom, fmt(wer)))
    lines.append("")
    lines.append("| Component | Edits | Share of frozen WER | WER points |")
    lines.append("| --- | --- | --- | --- |")
    lines.append("| Reading-order divergence (E0 - E_S) | %d | %.1f%% | %s |"
                 % (decomp["reading_order_edits"],
                    100 * decomp["reading_order_share_of_wer"],
                    fmt(decomp["reading_order_share_points"])))
    lines.append("| Tokenization divergence (E_S - E_SN) | %d | %.1f%% | %s |"
                 % (decomp["tokenization_edits"],
                    100 * decomp["tokenization_share_of_wer"],
                    fmt(decomp["tokenization_share_points"])))
    lines.append("| Residual token error (E_SN) | %d | %.1f%% | %s |"
                 % (decomp["residual_edits"],
                    100 * decomp["residual_share_of_wer"],
                    fmt(decomp["residual_share_points"])))
    lines.append("| Total (frozen WER) | %d | 100.0%% | %s |"
                 % (sum_e0, fmt(wer)))
    lines.append("")
    nm = [(row["doc"], row["e_sorted"] - row["e0"]) for row in per_doc
          if row["e_sorted"] > row["e0"]]
    nm_canon = [row["doc"] for row in per_doc
                if row["e_sorted_canon"] > row["e_sorted"]]
    lines.append("Method note: the decomposition is a micro-level "
                 "decomposition (edit counts summed over the 50 documents "
                 "before shares are taken). Per document the order step is "
                 "not guaranteed monotonic, because Levenshtein distance on "
                 "sorted sequences is a different alignment, not a bounded "
                 "relaxation: in %d of 50 documents sorting raised the count "
                 "slightly (%s; +%d edits in total across those documents), "
                 "more than offset by the other %d documents. The "
                 "tokenization step raised no document's count (%d "
                 "documents). The micro totals above are monotonic: "
                 "%d > %d > %d."
                 % (len(nm),
                    ", ".join("%s +%d" % (d, diff) for d, diff in nm),
                    sum(diff for _, diff in nm), 50 - len(nm),
                    len(nm_canon), sum_e0, sum_es, sum_esn))
    lines.append("")
    lines.append("The residual %s is the token error rate that survives "
                 "removing order and tokenization divergence: tokens whose "
                 "alphanumeric content itself differs (OCR character "
                 "misreads surfacing as whole-token mismatches, plus tokens "
                 "missed or invented outright). It is an upper bound on "
                 "pure character error read at token granularity, not a "
                 "character-level error rate."
                 % fmt(decomp["wer_residual"]))
    lines.append("")
    lines.append("Descriptive cross-checks (not part of the decomposition): "
                 "raw token multiset overlap is %d of %d reference tokens "
                 "(%s); after normalization C it is %d of %d canonical "
                 "reference tokens (%s). On document 82092117, the "
                 "one-document diagnostic of record, the raw overlap is "
                 "%d of %d reference tokens, and its counts are E0 %d, "
                 "E_S %d, E_SN %d."
                 % (sum_overlap_raw, sum_ref, fmt(sum_overlap_raw / sum_ref),
                    sum_overlap_canon, sum_ref_canon,
                    fmt(sum_overlap_canon / sum_ref_canon),
                    diag_82092117["overlap_raw"],
                    diag_82092117["ref_tokens"],
                    diag_82092117["e0"], diag_82092117["e_sorted"],
                    diag_82092117["e_sorted_canon"]))
    lines.append("")
    lines.append("## Per-document decomposition")
    lines.append("")
    lines.append("| Document | Ref tokens | E0 | E_S | E_SN | WER | Residual WER |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in per_doc:
        lines.append("| %s | %d | %d | %d | %d | %s | %s |" % (
            row["doc"], row["ref_tokens"], row["e0"], row["e_sorted"],
            row["e_sorted_canon"], fmt(row["wer"]),
            fmt(row["e_sorted_canon"] / row["ref_tokens"])
            if row["ref_tokens"] else "0.0000"))
    lines.append("")
    lines.append("Full machine-readable results: "
                 "results/amendment_a2_wer_decomposition.json; per-document "
                 "re-run records with token sequences: "
                 "results/amendment_a2_arm_a.jsonl; generator: "
                 "scripts/amendment_a2_diagnostic.py.")
    lines.append("")
    (RESULTS / "amendment_a2_report.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print("DONE mismatches:", len(mismatches))
    print(json.dumps(decomp, indent=2))


if __name__ == "__main__":
    main()
