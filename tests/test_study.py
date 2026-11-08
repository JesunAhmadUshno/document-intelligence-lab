import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import arm_a  # noqa: E402
import arm_b  # noqa: E402
import common  # noqa: E402
import make_results  # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_punctuation_runs_collapse(self):
        self.assertEqual(common.normalize("Fax:  (614) 466-5087"),
                         "fax 614 466 5087")

    def test_case_and_accents(self):
        self.assertEqual(common.normalize("  DATE: "), "date")
        self.assertEqual(common.normalize("Café"), "café")


class TestGroundTruth(unittest.TestCase):
    ANN = {"form": [
        {"id": 0, "label": "header", "text": "FAX", "words": [], "linking": []},
        {"id": 1, "label": "question", "text": "TO:", "words": [{"text": "TO:"}],
         "linking": [[1, 2]]},
        {"id": 2, "label": "answer", "text": "George", "words": [{"text": "George"}],
         "linking": [[1, 2]]},
        {"id": 3, "label": "other", "text": "x", "words": [], "linking": [[3, 2]]},
    ]}

    def test_pairs_only_question_answer(self):
        self.assertEqual(common.ground_truth_pairs(self.ANN),
                         [("TO:", "George")])

    def test_reference_tokens(self):
        self.assertEqual(common.reference_tokens(self.ANN),
                         ["to:", "george"])


class TestMatching(unittest.TestCase):
    def test_greedy_consumption(self):
        gt = [("TO:", "George"), ("TO:", "George"), ("DATE:", "12/10/98")]
        pred = [("to", "george"), ("TO:", "George"), ("TO:", "George"),
                ("Date", "12 /10 /98")]
        tp, npred, ntruth = common.match_pairs(pred, gt)
        self.assertEqual((tp, npred, ntruth), (3, 4, 3))

    def test_prf_zero(self):
        self.assertEqual(common.prf(0, 0, 5), (0.0, 0.0, 0.0))


class TestWer(unittest.TestCase):
    def test_known_distance(self):
        self.assertEqual(common.levenshtein(
            ["the", "cat", "sat"], ["the", "dog", "sat", "down"]), 2)

    def test_identical(self):
        self.assertEqual(common.wer_counts(["a", "b"], ["a", "b"]), (0, 2))


def line(*words):
    """Build an arm_a.Line from (text, left, width) triples on one row."""
    ws = [arm_a.Word(t, x, 0, w, 10) for (t, x, w) in words]
    return arm_a.Line(ws)


class TestExtraction(unittest.TestCase):
    def test_r1_same_line(self):
        pairs = arm_a.extract_pairs([line(("TO:", 0, 30), ("George", 60, 60))])
        self.assertEqual(pairs, [("TO", "George")])

    def test_r2_next_line(self):
        pairs = arm_a.extract_pairs([
            line(("DATE:", 0, 40)),
            line(("12/10/98", 0, 70)),
        ])
        self.assertEqual(pairs, [("DATE", "12/10/98")])

    def test_r2_skips_key_lines(self):
        pairs = arm_a.extract_pairs([
            line(("NAME:", 0, 45)),
            line(("FAX:", 0, 40)),
            line(("555-1234", 0, 80)),
        ])
        self.assertEqual(pairs, [("FAX", "555-1234")])

    def test_r3_wide_gap(self):
        pairs = arm_a.extract_pairs([
            line(("TOTAL", 0, 50), ("AMOUNT", 55, 55), ("DUE", 115, 35),
                 ("$5.00", 300, 50)),
        ])
        self.assertEqual(pairs, [("TOTAL AMOUNT DUE", "$5.00")])

    def test_no_pair_without_value(self):
        self.assertEqual(arm_a.extract_pairs([line(("HELLO", 0, 50))]), [])

    def test_tsv_parse_groups_lines(self):
        tsv = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
            "left\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t0\t0\t30\t10\t95\tTO:\n"
            "5\t1\t1\t1\t1\t2\t40\t0\t60\t10\t96\tGeorge\n"
            "5\t1\t1\t1\t2\t1\t0\t20\t40\t10\t90\tDATE:\n"
        )
        lines = arm_a.parse_tsv(tsv)
        self.assertEqual([ln.text for ln in lines], ["TO: George", "DATE:"])


class TestArmBParsing(unittest.TestCase):
    def test_plain_json(self):
        out = arm_b.parse_response_text(
            '[{"question": "TO:", "answer": "George"}]')
        self.assertEqual(out, [("TO:", "George")])

    def test_fenced_json(self):
        out = arm_b.parse_response_text(
            '```json\n[{"question": "A", "answer": "B"}]\n```')
        self.assertEqual(out, [("A", "B")])

    def test_garbage_is_failure(self):
        self.assertIsNone(arm_b.parse_response_text("no json here"))
        self.assertIsNone(arm_b.parse_response_text('{"question": "A"}'))
        self.assertIsNone(arm_b.parse_response_text('[{"question": 3, "answer": "B"}]'))

    def test_empty_fields_dropped(self):
        out = arm_b.parse_response_text(
            '[{"question": "A", "answer": " "}, {"question": "C", "answer": "D"}]')
        self.assertEqual(out, [("C", "D")])


class TestVerdicts(unittest.TestCase):
    BASE = {
        "arm_a": {"f1": 0.20, "wer": 0.12, "time": {"median": 1.0}},
        "arm_b": {"f1": 0.60, "time": {"median": 9.0}},
    }

    def test_all_confirmed(self):
        v = make_results.verdicts(self.BASE)
        self.assertEqual(v, {"H1": "CONFIRMED", "H2": "CONFIRMED",
                             "H3": "CONFIRMED"})

    def test_refuted(self):
        m = {"arm_a": {"f1": 0.50, "wer": 0.03, "time": {"median": 9.0}},
             "arm_b": {"f1": 0.45, "time": {"median": 8.0}}}
        v = make_results.verdicts(m)
        self.assertEqual(v, {"H1": "REFUTED", "H2": "REFUTED",
                             "H3": "REFUTED"})


if __name__ == "__main__":
    unittest.main()
