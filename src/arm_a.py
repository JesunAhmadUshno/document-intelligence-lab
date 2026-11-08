"""Arm A: Tesseract OCR plus the frozen deterministic extraction
rules R1 to R3 from PREREGISTRATION.md. No learned model anywhere
in this arm."""
import statistics
import subprocess
import time

from common import normalize


class Word:
    __slots__ = ("text", "left", "top", "width", "height")

    def __init__(self, text, left, top, width, height):
        self.text = text
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    @property
    def right(self):
        return self.left + self.width


class Line:
    __slots__ = ("words",)

    def __init__(self, words):
        self.words = words

    @property
    def text(self):
        return " ".join(w.text for w in self.words)


def parse_tsv(tsv_text):
    """Tesseract TSV to a list of Line objects in emission order.
    Words are level-5 rows with conf >= 0 and non-empty text."""
    lines = []
    by_key = {}
    for row in tsv_text.splitlines()[1:]:
        fields = row.split("\t")
        if len(fields) < 12:
            continue
        (level, _page, block, par, line_no, _word_no, left, top,
         width, height, conf, text) = fields[:12]
        if level != "5" or not text.strip():
            continue
        try:
            conf_val = float(conf)
            word = Word(text, int(left), int(top), int(width), int(height))
        except ValueError:
            continue
        if conf_val < 0:
            continue
        key = (block, par, line_no)
        if key not in by_key:
            by_key[key] = Line([])
            lines.append(by_key[key])
        by_key[key].words.append(word)
    return [ln for ln in lines if ln.words]


def _has_letter(text):
    return any(ch.isalpha() for ch in text)


def r1_prefix(line):
    """Key prefix before the first ':' if the R1 conditions hold."""
    text = line.text
    if ":" not in text:
        return None
    prefix = text.split(":", 1)[0]
    if 1 <= len(prefix.split()) <= 6 and len(prefix) <= 45 and _has_letter(prefix):
        return prefix.strip()
    return None


def r2_body(line):
    """Line text without the trailing ':' if the R2 conditions hold."""
    text = line.text
    if not text.endswith(":"):
        return None
    body = text[:-1]
    if len(body.split()) <= 8 and len(body) <= 60 and _has_letter(body):
        return body.strip()
    return None


def qualifies_as_key(line):
    return r1_prefix(line) is not None or r2_body(line) is not None


def _r3_pair(line):
    words = line.words
    if len(words) < 3:
        return None
    gaps = [words[i + 1].left - words[i].right for i in range(len(words) - 1)]
    widest = max(range(len(gaps)), key=lambda i: gaps[i])
    if gaps[widest] < 40 or gaps[widest] < 2.0 * statistics.median(gaps):
        return None
    left = " ".join(w.text for w in words[:widest + 1])
    right = " ".join(w.text for w in words[widest + 1:])
    if not (1 <= len(left.split()) <= 6 and len(left) <= 45
            and _has_letter(left) and right.strip()):
        return None
    return (left, right)


def extract_pairs(lines):
    """The frozen rules, applied in reading order, R1 then R2
    then R3. A consumed line is never reused."""
    consumed = [False] * len(lines)
    pairs = []
    for i, line in enumerate(lines):
        if consumed[i]:
            continue
        key = None
        prefix = r1_prefix(line)
        if prefix is not None:
            rest = line.text.split(":", 1)[1].strip()
            if rest:
                pairs.append((prefix, rest))
                consumed[i] = True
                continue
            key = prefix
        if key is None:
            key = r2_body(line)
        if key is not None:
            # Value search per Amendment A1 (DECISIONS.md): scan in
            # order, stop at the first key line; only non-key lines
            # before that boundary are candidates.
            for j in range(i + 1, min(i + 4, len(lines))):
                cand = lines[j]
                if qualifies_as_key(cand):
                    break
                if consumed[j] or not cand.text.strip():
                    continue
                pairs.append((key, cand.text))
                consumed[i] = True
                consumed[j] = True
                break
            continue
        pair = _r3_pair(line)
        if pair is not None:
            pairs.append(pair)
            consumed[i] = True
    seen = set()
    unique = []
    for key, value in pairs:
        probe = (normalize(key), normalize(value))
        if probe not in seen:
            seen.add(probe)
            unique.append((key, value))
    return unique


def run_tesseract(image, tesseract_cmd):
    proc = subprocess.run(
        [tesseract_cmd, str(image), "stdout", "tsv"],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError("tesseract failed: " + proc.stderr.strip()[:200])
    return proc.stdout


def run_document(image, tesseract_cmd):
    """One document through Arm A. Returns the JSONL record fields
    (minus doc id and WER, which the driver adds)."""
    start = time.perf_counter()
    tsv = run_tesseract(image, tesseract_cmd)
    lines = parse_tsv(tsv)
    pairs = extract_pairs(lines)
    seconds = time.perf_counter() - start
    hyp_tokens = []
    for line in lines:
        for word in line.words:
            hyp_tokens.extend(word.text.lower().split())
    return {
        "pairs": [[k, v] for k, v in pairs],
        "seconds": seconds,
        "ocr_words": len(hyp_tokens),
        "hyp_tokens": hyp_tokens,
    }
