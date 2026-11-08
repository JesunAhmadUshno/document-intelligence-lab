"""Driver: run Arm A and/or Arm B over the FUNSD test split.

Writes one JSONL record per document per arm, appending and
flushing so an interrupted run loses nothing; documents already
present in an arm's output file are skipped (resume)."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import arm_a  # noqa: E402
import arm_b  # noqa: E402
import common  # noqa: E402


def _done_ids(path):
    done = set()
    if Path(path).exists():
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                done.add(json.loads(line)["doc"])
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["a", "b", "both"], default="both")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--tesseract", default="scripts/tesseract.sh")
    args = ap.parse_args()

    doc_ids = common.test_doc_ids(args.data_dir)
    if args.limit:
        doc_ids = doc_ids[:args.limit]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "started_unix": time.time(),
        "documents": doc_ids,
        "arm_b_model": arm_b.MODEL,
    }
    try:
        manifest["tesseract_version"] = subprocess.run(
            [args.tesseract, "--version"], capture_output=True,
            text=True).stdout.splitlines()[0]
    except Exception as exc:
        manifest["tesseract_version"] = "unavailable: %s" % exc

    if args.arm in ("a", "both"):
        path = out_dir / "arm_a.jsonl"
        done = _done_ids(path)
        with open(path, "a", encoding="utf-8") as fh:
            for doc_id in doc_ids:
                if doc_id in done:
                    continue
                ann = common.load_annotation(
                    common.annotation_path(args.data_dir, doc_id))
                rec = arm_a.run_document(
                    common.image_path(args.data_dir, doc_id),
                    args.tesseract)
                hyp = rec.pop("hyp_tokens")
                edits, ref_n = common.wer_counts(
                    common.reference_tokens(ann), hyp)
                record = {
                    "doc": doc_id,
                    "pairs": rec["pairs"],
                    "seconds": rec["seconds"],
                    "ocr_words": rec["ocr_words"],
                    "wer_edits": edits,
                    "ref_tokens": ref_n,
                }
                fh.write(json.dumps(record) + "\n")
                fh.flush()
                print("A", doc_id, len(record["pairs"]), flush=True)

    if args.arm in ("b", "both"):
        path = out_dir / "arm_b.jsonl"
        done = _done_ids(path)
        with open(path, "a", encoding="utf-8") as fh:
            for doc_id in doc_ids:
                if doc_id in done:
                    continue
                rec = arm_b.run_document(
                    common.image_path(args.data_dir, doc_id))
                rec = {"doc": doc_id, **rec}
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                print("B", doc_id, len(rec["pairs"]),
                      "failed" if rec["failed"] else "ok", flush=True)

    manifest["finished_unix"] = time.time()
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
