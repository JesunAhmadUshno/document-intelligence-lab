"""Amendment A4 rescoring: merge the Amendment A3 Arm B
completion records over the failed records in the frozen
results/arm_b.jsonl and recompute the full-50 headline numbers
and the H1/H3 verdicts with scripts/make_results.py's own logic
(its compute and verdicts functions, fed the merged record set
through a temporary results directory).

Self-check first: make_results.compute on the frozen inputs
must reproduce results/metrics.json exactly; if it does not,
this script raises and writes nothing. The merged run must
also reproduce the frozen Arm A figures exactly, since Arm A
is fed from the frozen records unchanged.

Outputs (new files only): results/amendment_rescoring.json and
results/amendment_rescoring_report.md. RESULTS.md,
results/metrics.json, results/arm_a.jsonl, and
results/arm_b.jsonl are not modified."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import make_results  # noqa: E402


def main():
    data_dir = str(ROOT / "data")
    results_dir = ROOT / "results"
    frozen_metrics = json.loads(
        (results_dir / "metrics.json").read_text(encoding="utf-8"))

    # Self-check: the frozen generator's logic on the frozen
    # inputs reproduces the committed metrics exactly.
    check_metrics, _ = make_results.compute(data_dir, str(results_dir))
    assert check_metrics == frozen_metrics, (
        "self-check failed: make_results.compute on the frozen "
        "inputs does not reproduce results/metrics.json exactly")
    print("self-check: make_results.compute reproduces "
          "results/metrics.json exactly from the frozen inputs")

    arm_b_frozen = make_results._load_jsonl(results_dir / "arm_b.jsonl")
    completion = make_results._load_jsonl(
        results_dir / "amendment_arm_b_completion.jsonl")
    frozen_failed = sorted(
        d for d, r in arm_b_frozen.items() if r["failed"])
    assert sorted(completion) == frozen_failed, (
        "completion records do not cover exactly the frozen "
        "failed documents")
    still_failed = sorted(
        d for d in frozen_failed if completion[d]["failed"])
    answered_now = sorted(
        d for d in frozen_failed if not completion[d]["failed"])

    merged_b = dict(arm_b_frozen)
    for doc_id in frozen_failed:
        merged_b[doc_id] = completion[doc_id]
    assert len(merged_b) == len(arm_b_frozen) == 50

    # Feed the merged set through make_results.compute unchanged:
    # a temporary results directory holding the frozen Arm A file
    # and the merged Arm B file under the frozen names.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "arm_a.jsonl").write_bytes(
            (results_dir / "arm_a.jsonl").read_bytes())
        with open(tmp / "arm_b.jsonl", "w", encoding="utf-8") as fh:
            for doc_id in sorted(merged_b):
                fh.write(json.dumps(merged_b[doc_id]) + "\n")
        merged_metrics, _rows = make_results.compute(data_dir, str(tmp))

    assert merged_metrics["arm_a"] == frozen_metrics["arm_a"], (
        "Arm A figures changed under the merged run")
    assert merged_metrics["documents_expected"] == 50
    assert merged_metrics["arm_b_documents"] == 50

    fa, fb = frozen_metrics["arm_b"], merged_metrics["arm_b"]
    fv, mv = frozen_metrics["verdicts"], merged_metrics["verdicts"]
    out = {
        "amendment": "A4 (2026-11-17)",
        "self_check": ("make_results.compute on the frozen inputs "
                       "reproduces results/metrics.json exactly"),
        "merge": {
            "frozen_failed_documents": len(frozen_failed),
            "completion_records_merged": len(frozen_failed),
            "answered_now": len(answered_now),
            "still_failed_zero_pair": still_failed,
            "frozen_answered_documents_kept": 50 - len(frozen_failed),
        },
        "arm_a_unchanged": merged_metrics["arm_a"],
        "arm_b_merged": {k: fb_ for k, fb_ in merged_metrics["arm_b"].items()},
        "arm_b_frozen": fa,
        "verdicts_merged": mv,
        "verdicts_frozen": fv,
        "rows": merged_metrics["rows"],
    }
    (results_dir / "amendment_rescoring.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")

    fmt = make_results._fmt
    a = merged_metrics["arm_a"]
    lines = [
        "# Amendment A4: full-50 Arm B rescoring",
        "",
        "Registered in DECISIONS.md as Amendment A4 (2026-11-17).",
        "Computed by scripts/amendment_rescoring.py with",
        "scripts/make_results.py's own compute and verdicts logic,",
        "after that logic reproduced results/metrics.json exactly",
        "from the frozen inputs. The merged Arm B set is the frozen",
        "results/arm_b.jsonl with the %d failed records replaced by"
        % len(frozen_failed),
        "results/amendment_arm_b_completion.jsonl (Amendment A3);",
        "the %d documents still unanswered keep failed records with"
        % len(still_failed),
        "zero predicted pairs. Arm A is the frozen record, unchanged.",
        "",
        "## Merged headline numbers (all 50 documents)",
        "",
        "| Measure | Arm A: Tesseract + rules | Arm B: Gemini vision (merged) |",
        "| --- | --- | --- |",
        "| Field precision (micro) | %s | %s |"
        % (fmt(a["precision"]), fmt(fb["precision"])),
        "| Field recall (micro) | %s | %s |"
        % (fmt(a["recall"]), fmt(fb["recall"])),
        "| Field F1 (micro) | %s | %s |" % (fmt(a["f1"]), fmt(fb["f1"])),
        "| True positives / predicted / ground truth | %d / %d / %d | %d / %d / %d |"
        % (a["tp"], a["predicted"], a["truth"],
           fb["tp"], fb["predicted"], fb["truth"]),
        "| Median seconds per document | %s | %s |"
        % (fmt(a["time"]["median"], 3), fmt(fb["time"]["median"], 3)),
        "| Mean seconds per document | %s | %s |"
        % (fmt(a["time"]["mean"], 3), fmt(fb["time"]["mean"], 3)),
        "| Time IQR (seconds) | %s | %s |"
        % (fmt(a["time"]["iqr"], 3), fmt(fb["time"]["iqr"], 3)),
        "",
        "Arm B merged: %d API calls for 50 documents; %d failed "
        "documents (counted, with zero predicted pairs, never "
        "dropped): %s."
        % (fb["calls"], fb["failures"], ", ".join(still_failed)),
        "",
        "Arm A figures are identical to the frozen record "
        "(P %s, R %s, F1 %s, WER %s), so H2 stands as frozen: **%s**."
        % (fmt(a["precision"]), fmt(a["recall"]), fmt(a["f1"]),
           fmt(a["wer"]), mv["H2"]),
        "",
        "## Verdicts under the frozen pass lines",
        "",
        "- H1 (vision-LLM beats classical on field F1 by at least "
        "0.15): **%s**. Merged F1 difference is %s (frozen: %s, "
        "verdict %s)."
        % (mv["H1"], fmt(fb["f1"] - a["f1"]),
           fmt(fa["f1"] - a["f1"]), fv["H1"]),
        "- H3 (classical arm at least 5 times faster per document): "
        "**%s**. Merged median times: Arm A %s s, Arm B %s s "
        "(ratio %s; merged Arm B mean %s s, IQR %s s). Frozen: "
        "Arm B median %s s, verdict %s."
        % (mv["H3"], fmt(a["time"]["median"], 3),
           fmt(fb["time"]["median"], 3),
           fmt(fb["time"]["median"] / a["time"]["median"], 2),
           fmt(fb["time"]["mean"], 3), fmt(fb["time"]["iqr"], 3),
           fmt(fa["time"]["median"], 3), fv["H3"]),
        "",
        "## What this record supersedes",
        "",
        "For a future paper version, this merged record supersedes",
        "the frozen Arm B headline numbers (P %s, R %s, F1 %s;"
        % (fmt(fa["precision"]), fmt(fa["recall"]), fmt(fa["f1"])),
        "%d failed documents) and the frozen H1 and H3 verdicts"
        % fa["failures"],
        "wherever they differ above. The frozen RESULTS.md and",
        "results/metrics.json stay untouched on disk as the record",
        "of the original run; nothing in this amendment rewrites",
        "them.",
        "",
    ]
    (results_dir / "amendment_rescoring_report.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print("wrote results/amendment_rescoring.json and "
          "results/amendment_rescoring_report.md")
    print("merged Arm B: P %.4f, R %.4f, F1 %.4f (TP %d / pred %d "
          "/ GT %d); failures %d; verdicts %s"
          % (fb["precision"], fb["recall"], fb["f1"], fb["tp"],
             fb["predicted"], fb["truth"], fb["failures"], mv))


if __name__ == "__main__":
    main()
