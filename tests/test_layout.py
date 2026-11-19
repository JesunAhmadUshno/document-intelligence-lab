"""Portfolio standard checks: the lock holds, the required files exist,
and no public file carries a grade."""
import glob
import hashlib
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SHA-256 of PREREGISTRATION.md as committed in 0774bfd (tag proposal-v1), before any code or run.
LOCKED_SHA256 = "c9b23f2c05964d176fba24796dd7efeaafbee608c777220dc94f7b55807b56ae"


class TestLayout(unittest.TestCase):
    def test_preregistration_is_unchanged_since_the_lock(self):
        with open(os.path.join(ROOT, "PREREGISTRATION.md"), "rb") as f:
            self.assertEqual(
                hashlib.sha256(f.read()).hexdigest(), LOCKED_SHA256,
                "PREREGISTRATION.md changed after its lock; record an amendment in DECISIONS.md instead")

    def test_required_files_exist(self):
        need = ["README.md", "PREREGISTRATION.md", "REPORT.md", "RESULTS.md", "DECISIONS.md",
                "CHANGELOG.md", "CITATION.cff", "SECURITY.md", "LICENSE",
                "results/arm_a.jsonl", "results/arm_b.jsonl", "results/metrics.json"]
        missing = [p for p in need if not os.path.exists(os.path.join(ROOT, p))]
        self.assertFalse(missing, "missing: " + ", ".join(missing))

    def test_readme_opens_with_the_abstract(self):
        text = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
        for field in ("**Question.**", "**Headline.**", "**Field.**", "**Job family.**",
                      "**Verdict.**", "## Lifecycle", "## Layout"):
            self.assertIn(field, text)

    def test_no_public_grade(self):
        files = glob.glob(os.path.join(ROOT, "*.md")) + glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True)
        for path in files:
            text = open(path, encoding="utf-8").read()
            for mark in ("of 10,000", "/10000", "/10,000", "Grade:", "## Grade"):
                self.assertNotIn(mark, text, os.path.basename(path) + " carries a grade; grades are internal")


if __name__ == "__main__":
    unittest.main()
