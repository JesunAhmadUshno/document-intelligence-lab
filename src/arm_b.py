"""Arm B: field extraction by a Gemini vision model, reached only
through the existing connected Gemini connector route
(custom.legacy-gemini), following that connector's documented call
pattern: the credential is attached by the dynamic-credentials
helper under the stored name custom.gemini, and requests go only
to generativelanguage.googleapis.com."""
import base64
import json
import sys
import time
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import (  # noqa: E402
    add_surrogate_to_request,
    read_json_response,
)

MODEL = "gemini-3-flash-preview"
API_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + MODEL + ":generateContent")

PROMPT = (
    "You are extracting fields from a scanned form. List every field "
    "on the form as a JSON array of objects with exactly two keys: "
    "\"question\" and \"answer\". The question is the printed field "
    "label, transcribed exactly as printed, including any trailing "
    "colon. The answer is the value belonging to that label, "
    "transcribed exactly as it appears. Include only fields where "
    "both a label and a value are present. Do not invent values. Do "
    "not include headers, titles, or body text that are not field "
    "labels with values. Respond with the JSON array only, no other "
    "text."
)


def parse_response_text(text):
    """Frozen parsing: strip code fences, parse JSON, keep objects
    whose question and answer are both non-empty strings. Returns
    the pair list, or None on any parse failure."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, list):
        return None
    pairs = []
    for item in data:
        if not isinstance(item, dict):
            return None
        q = item.get("question")
        a = item.get("answer")
        if not isinstance(q, str) or not isinstance(a, str):
            return None
        if q.strip() and a.strip():
            pairs.append((q, a))
    return pairs


def _call(image_bytes):
    body = json.dumps({
        "contents": [{"parts": [
            {"inline_data": {
                "mime_type": "image/png",
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"temperature": 0},
    }).encode()
    request = urllib.request.Request(
        API_URL, data=body, headers={"Content-Type": "application/json"})
    add_surrogate_to_request(
        request, "custom.gemini",
        allowed_hosts=["generativelanguage.googleapis.com"])
    with urllib.request.urlopen(request, timeout=180) as response:
        return read_json_response(response)


def run_document(image):
    """One document through Arm B, with the frozen failure rules:
    one retry after 5 seconds on error; a document that still
    fails or does not parse contributes zero pairs and is counted
    as failed."""
    start = time.perf_counter()
    image_bytes = open(image, "rb").read()
    calls = 0
    last_error = ""
    for attempt in (1, 2):
        calls += 1
        try:
            data = _call(image_bytes)
        except Exception as exc:  # HTTP error, timeout, transport
            last_error = "%s: %s" % (type(exc).__name__, str(exc)[:160])
            if attempt == 1:
                time.sleep(5)
                continue
            return _record([], time.perf_counter() - start, calls,
                           True, last_error, None)
        model_version = data.get("modelVersion")
        parts = []
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                if "text" in part:
                    parts.append(part["text"])
        pairs = parse_response_text("".join(parts)) if parts else None
        if pairs is None:
            return _record([], time.perf_counter() - start, calls,
                           True, "unparseable response", model_version)
        return _record([[k, v] for k, v in pairs],
                       time.perf_counter() - start, calls,
                       False, "", model_version)
    raise AssertionError("unreachable")


def _record(pairs, seconds, calls, failed, error, model_version):
    return {
        "pairs": pairs,
        "seconds": seconds,
        "calls": calls,
        "failed": failed,
        "error": error,
        "model_version": model_version,
    }
