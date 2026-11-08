"""Shared ground-truth loading, normalization, and scoring.

Both arms and the results generator use these exact functions, so
the rules frozen in PREREGISTRATION.md cannot drift between the
arm that produces pairs and the code that scores them.
"""
import json
import unicodedata
from collections import Counter
from pathlib import Path


def normalize(text):
    """The frozen normalization N(s) from PREREGISTRATION.md:
    NFKC, lowercase, every maximal run of characters that are not
    letters or digits becomes one space, ends stripped."""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    chars = [ch if ch.isalnum() else " " for ch in text]
    return " ".join("".join(chars).split())


def load_annotation(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def ground_truth_pairs(annotation):
    """Frozen pair construction: one (question, answer) text pair
    per linking pair joining a question block and an answer block,
    deduplicated, in first-appearance order."""
    blocks = {b["id"]: b for b in annotation["form"]}
    pairs = []
    seen = set()
    for block in annotation["form"]:
        for link in block.get("linking", []):
            a = blocks.get(link[0])
            b = blocks.get(link[1])
            if a is None or b is None:
                continue
            if {a["label"], b["label"]} != {"question", "answer"}:
                continue
            q = a if a["label"] == "question" else b
            v = b if q is a else a
            pair = (q["text"], v["text"])
            if pair not in seen:
                seen.add(pair)
                pairs.append(pair)
    return pairs


def reference_tokens(annotation):
    """Frozen WER reference: words of the blocks in form order,
    words in listed order, lowercased, split on whitespace."""
    tokens = []
    for block in annotation["form"]:
        for word in block.get("words", []):
            tokens.extend(word["text"].lower().split())
    return tokens


def match_pairs(predicted, ground_truth):
    """Greedy multiset matching under the frozen rule.

    Returns (true_positives, n_predicted, n_ground_truth)."""
    available = Counter((normalize(k), normalize(v)) for k, v in ground_truth)
    tp = 0
    for key, value in predicted:
        probe = (normalize(key), normalize(value))
        if available.get(probe, 0) > 0:
            available[probe] -= 1
            tp += 1
    return tp, len(predicted), len(ground_truth)


def prf(tp, n_predicted, n_truth):
    precision = tp / n_predicted if n_predicted else 0.0
    recall = tp / n_truth if n_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def levenshtein(a, b):
    """Token-sequence edit distance (substitution cost 1)."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (0 if ca == cb else 1),
            ))
        previous = current
    return previous[-1]


def wer_counts(reference, hypothesis):
    """(edit distance, reference token count) for one document."""
    return levenshtein(reference, hypothesis), len(reference)


def test_doc_ids(data_dir):
    """Document ids of the published test split, sorted."""
    ann_dir = Path(data_dir) / "funsd" / "dataset" / "testing_data" / "annotations"
    return sorted(p.stem for p in ann_dir.glob("*.json"))


def annotation_path(data_dir, doc_id):
    return (Path(data_dir) / "funsd" / "dataset" / "testing_data"
            / "annotations" / (doc_id + ".json"))


def image_path(data_dir, doc_id):
    return (Path(data_dir) / "funsd" / "dataset" / "testing_data"
            / "images" / (doc_id + ".png"))
