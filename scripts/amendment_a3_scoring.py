"""Amendment A3 scoring: score the Arm B completion records with
the frozen scorer (src/common.py, as scripts/make_results.py
uses it) and set them beside (i) the committed Arm A records for
the same documents and (ii) the frozen figures for the 21
documents the original Arm B run answered.

Self-check first: the per-document scoring of the frozen records
must reproduce results/metrics.json rows exactly for both arms;
if it does not, this script raises and writes nothing.

Outputs (new files only): results/amendment_a3_scoring.json and
results/amendment_a3_report.md. No frozen file is modified and
no frozen verdict is recomputed."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import common  # noqa: E402


def _load_jsonl(path):
    records = {}
    if Path(path).exists():
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                rec = json.loads(line)
                records[rec["doc"]] = rec
    return records


def _score(records, doc_ids, data_dir):
    """Micro P/R/F1 of one arm's records over doc_ids, plus
    per-document rows, using the frozen scorer."""
    tp = pred = truth = 0
    rows = []
    for doc_id in doc_ids:
        ann = common.load_annotation(
            common.annotation_path(data_dir, doc_id))
        gt = common.ground_truth_pairs(ann)
        rec = records[doc_id]
        t, p, n = common.match_pairs(
            [tuple(pair) for pair in rec["pairs"]], gt)
        _, _, f1 = common.prf(t, p, n)
        tp += t; pred += p; truth += n
        rows.append({"doc": doc_id, "truth": n, "pred": p, "tp": t,
                     "f1": f1, "seconds": rec["seconds"],
                     "failed": rec.get("failed", False)})
    p_, r_, f1_ = common.prf(tp, pred, truth)
    return {"tp": tp, "predicted": pred, "truth": truth,
            "precision": p_, "recall": r_, "f1": f1_}, rows


def main():
    data_dir = str(ROOT / "data")
    doc_ids = common.test_doc_ids(data_dir)
    arm_a = _load_jsonl(ROOT / "results" / "arm_a.jsonl")
    arm_b_frozen = _load_jsonl(ROOT / "results" / "arm_b.jsonl")
    completion = _load_jsonl(
        ROOT / "results" / "amendment_arm_b_completion.jsonl")
    metrics = json.loads(
        (ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))

    # Self-check against the frozen generator's committed rows.
    frozen_rows = {r["doc"]: r for r in metrics["rows"]}
    for arm, records in (("a", arm_a), ("b", arm_b_frozen)):
        _, rows = _score(records, doc_ids, data_dir)
        for row in rows:
            fr = frozen_rows[row["doc"]]
            assert row["truth"] == fr["truth"], (arm, row["doc"])
            assert row["pred"] == fr["%s_pred" % arm], (arm, row["doc"])
            assert row["tp"] == fr["%s_tp" % arm], (arm, row["doc"])
    print("self-check: per-document scoring reproduces "
          "results/metrics.json for all 50 documents, both arms")

    answered_frozen = [d for d in doc_ids if not arm_b_frozen[d]["failed"]]
    missing = [d for d in doc_ids if arm_b_frozen[d]["failed"]]
    attempted = [d for d in missing if d in completion]
    answered_now = [d for d in attempted if not completion[d]["failed"]]
    still_failed = [d for d in attempted if completion[d]["failed"]]
    not_attempted = [d for d in missing if d not in completion]

    b21, _ = _score(arm_b_frozen, answered_frozen, data_dir)
    b_new, b_new_rows = _score(completion, answered_now, data_dir)
    a_new, a_new_rows = _score(arm_a, answered_now, data_dir)
    b_29, _ = _score(
        {d: completion.get(d, {"pairs": [], "seconds": 0.0,
                                "failed": True}) for d in missing},
        missing, data_dir)
    a_29, _ = _score(arm_a, missing, data_dir)

    out = {
        "amendment": "A3 (2026-11-17)",
        "frozen_run_answered_documents": {
            "documents": len(answered_frozen), "arm_b": b21},
        "completion": {
            "missing_documents": len(missing),
            "attempted": len(attempted),
            "answered_now": len(answered_now),
            "still_failed": still_failed,
            "not_attempted": not_attempted,
            "arm_b_on_answered_now": b_new,
            "arm_a_on_same_documents": a_new,
            "arm_b_on_all_missing_attempted_zero_for_failures": b_29,
            "arm_a_on_all_missing": a_29,
            "per_document": [
                {"doc": brow["doc"], "truth": brow["truth"],
                 "b_pred": brow["pred"], "b_tp": brow["tp"],
                 "b_f1": brow["f1"], "b_seconds": brow["seconds"],
                 "a_pred": arow["pred"], "a_tp": arow["tp"],
                 "a_f1": arow["f1"]}
                for brow, arow in zip(b_new_rows, a_new_rows)],
        },
    }
    (ROOT / "results" / "amendment_a3_scoring.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")

    def fmt(m):
        return ("P %.4f, R %.4f, F1 %.4f (TP %d / pred %d / GT %d)"
                % (m["precision"], m["recall"], m["f1"],
                   m["tp"], m["predicted"], m["truth"]))

    lines = [
        "# Amendment A3: Arm B paced completion, scoring",
        "",
        "Registered in DECISIONS.md as Amendment A3 (2026-11-17).",
        "Scored with the frozen scorer (src/common.py), verified",
        "against results/metrics.json for all 50 documents before",
        "any subset figure was computed. Frozen verdicts are not",
        "recomputed here.",
        "",
        "## Outcome",
        "",
        "- Missing documents in the frozen run: %d (27 HTTP 429, "
        "2 timeouts)." % len(missing),
        "- Attempted in this completion: %d." % len(attempted),
        "- Answered now: %d." % len(answered_now),
        "- Still failed: %d%s." % (
            len(still_failed),
            (": " + ", ".join(still_failed)) if still_failed else ""),
        "- Not attempted (stop rule): %d%s." % (
            len(not_attempted),
            (": " + ", ".join(not_attempted)) if not_attempted else ""),
        "",
        "## Figures",
        "",
        "- Frozen run, the 21 documents it answered, Arm B: %s."
        % fmt(b21),
        "- Completion, the %d documents answered now, Arm B: %s."
        % (len(answered_now), fmt(b_new)),
        "- Same %d documents, committed Arm A: %s."
        % (len(answered_now), fmt(a_new)),
        "- All %d missing documents (completion failures counted "
        "as zero pairs), Arm B: %s." % (len(missing), fmt(b_29)),
        "- All %d missing documents, committed Arm A: %s."
        % (len(missing), fmt(a_29)),
        "",
        "## Per-document (documents answered in this completion)",
        "",
        "| Document | GT | B pred | B TP | B F1 | B s | A pred | "
        "A TP | A F1 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in out["completion"]["per_document"]:
        lines.append(
            "| %s | %d | %d | %d | %.3f | %.2f | %d | %d | %.3f |"
            % (row["doc"], row["truth"], row["b_pred"], row["b_tp"],
               row["b_f1"], row["b_seconds"], row["a_pred"],
               row["a_tp"], row["a_f1"]))
    lines += [
        "",
        "## What the full-50 comparison needs next",
        "",
        "A separate rescoring record, under its own amendment,",
        "that merges the completion records in",
        "results/amendment_arm_b_completion.jsonl with the frozen",
        "records in results/arm_b.jsonl (completion records",
        "replacing the failed frozen ones) and recomputes the",
        "headline Arm B numbers and the H1/H3 verdicts with",
        "scripts/make_results.py's logic, writing to new files",
        "only. Until that record exists, the frozen headline",
        "numbers in RESULTS.md stand as the study's record.",
        "",
    ]
    (ROOT / "results" / "amendment_a3_report.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print("wrote results/amendment_a3_scoring.json and "
          "results/amendment_a3_report.md")
    print("answered now: %d of %d attempted; frozen-21 Arm B F1 "
          "%.4f; completion-subset Arm B F1 %.4f; Arm A on the "
          "same documents F1 %.4f"
          % (len(answered_now), len(attempted), b21["f1"],
             b_new["f1"], a_new["f1"]))


if __name__ == "__main__":
    main()
