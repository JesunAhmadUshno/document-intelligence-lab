# Decisions and amendments

## D1: Tesseract runs from a user-space install

This VM has no system Tesseract and no sudo. Rather than
substituting a different OCR engine, Tesseract 5.3.4 (the Ubuntu
tesseract-ocr package, with tesseract-ocr-eng 4.1.0 language data)
is installed in user space: packages fetched with a user-space
apt state directory and unpacked with dpkg -x under
.tools/tesseract-root, launched through scripts/tesseract.sh with
LD_LIBRARY_PATH and TESSDATA_PREFIX set. Arm A is therefore the
real Tesseract the pre-registration names, not a substitute
engine. scripts/setup_tesseract.sh reproduces the install. The
version string is recorded in results/run_manifest.json.

## D2: Arm B calls carry a hard deadline in the client

During the full run, one document's Gemini call sat in flight
far beyond the intended 180-second timeout: a urllib socket
timeout does not bound a slow-drip response. The client now runs
each attempt on a daemon thread with a hard 180-second join
deadline; exceeding it raises a timeout, which the frozen failure
rule already covers (one retry, then the document is failed and
counted). This is a harness correction, not a protocol change:
the pre-registration freezes the failure semantics, and the
client now actually enforces them. The stuck attempt produced no
record and no number; the document was re-run under the fixed
client.

## Amendment A1 to PREREGISTRATION.md (before any measured run)

R2's value search, as originally written, continues past an
intervening key line and can assign that key's value to an
earlier key (example: lines "NAME:", "FAX:", "555-1234" would
pair NAME with the number and leave FAX valueless). That is a
defect in the rule text, found by a unit test before any run.
Amended rule: the value search scans later lines in order and
stops at the first line that qualifies as a key under R1 or R2;
only non-key lines before that boundary are candidates. No
measured run precedes this amendment; every run in this
repository uses the amended rule.
