"""Amendment A3 driver: paced completion of Arm B over the 29
documents the frozen run failed (27 HTTP 429, 2 timeouts).

Registered in DECISIONS.md as Amendment A3 (2026-11-17). Uses
src/arm_b.py unchanged (same route, model, prompt, and frozen
within-document failure rule). Adds only the registered pacing
(at least 5 seconds between documents) and the registered stop
rule (five consecutive documents ending in an HTTP 429 failure
stops the run). Output goes to
results/amendment_arm_b_completion.jsonl only; the frozen
results/arm_b.jsonl is read, never written. Documents already
present in the output file are skipped (resume)."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import arm_b  # noqa: E402
import common  # noqa: E402

PACE_SECONDS = 5
STOP_AFTER_CONSECUTIVE_429 = 5
ROUTE_BLOCKER_MARK = "credential helper is not available"


def _load_jsonl(path):
    records = {}
    if Path(path).exists():
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                rec = json.loads(line)
                records[rec["doc"]] = rec
    return records


def main():
    data_dir = str(ROOT / "data")
    frozen = _load_jsonl(ROOT / "results" / "arm_b.jsonl")
    out_path = ROOT / "results" / "amendment_arm_b_completion.jsonl"
    done = _load_jsonl(out_path)

    todo = [doc_id for doc_id in common.test_doc_ids(data_dir)
            if frozen.get(doc_id, {}).get("failed") and doc_id not in done]
    print("A3 completion: %d documents to attempt (%d already in "
          "the completion file)" % (len(todo), len(done)), flush=True)

    consecutive_429 = 0
    attempted = 0
    for doc_id in todo:
        if attempted:
            time.sleep(PACE_SECONDS)
        rec = arm_b.run_document(common.image_path(data_dir, doc_id))
        rec = {"doc": doc_id, **rec}
        with open(out_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
        attempted += 1
        print("B", doc_id, len(rec["pairs"]),
              "failed" if rec["failed"] else "ok",
              ("err: " + rec["error"]) if rec["failed"] else "",
              flush=True)
        if rec["failed"] and ROUTE_BLOCKER_MARK in rec["error"]:
            print("ROUTE BLOCKER: the connector credential helper "
                  "is unavailable; stopping. This is a route "
                  "failure, not a study result.", flush=True)
            return 3
        if rec["failed"] and "429" in rec["error"]:
            consecutive_429 += 1
            if consecutive_429 >= STOP_AFTER_CONSECUTIVE_429:
                print("STOP RULE: %d consecutive documents ended "
                      "in HTTP 429; stopping with a partial count."
                      % consecutive_429, flush=True)
                return 2
        else:
            consecutive_429 = 0
    print("A3 completion finished: %d documents attempted in this "
          "invocation." % attempted, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
