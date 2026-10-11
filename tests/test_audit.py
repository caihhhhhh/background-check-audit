"""Tests for bg_audit.py — timeline parsing, checks, ledger validation, report."""

import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import bg_audit as audit


def make_audit(resume_text: str) -> Path:
    tmp = Path(tempfile.mkdtemp())
    resume = tmp / "resume.txt"
    resume.write_text(resume_text, encoding="utf-8")
    audit.command_new(Namespace(
        resume=resume, name="demo", output_dir=tmp, force=False,
    ))
    return tmp / "demo"


class TimelineTest(unittest.TestCase):
    def test_parses_common_formats(self):
        text = "MEXC 2025.09 – 至今\nAllcosmos 2023年6月 - 2025年8月\nTec-do 2021-07 ~ 2022.05"
        ranges = audit.parse_ranges(text, today=(2026, 10))
        self.assertEqual(len(ranges), 3)
        self.assertEqual(ranges[0]["start_index"], 2025 * 12 + 8)
        self.assertEqual(ranges[0]["end_index"], 2026 * 12 + 9)
        self.assertFalse(ranges[0]["fuzzy"])

    def test_year_only_is_fuzzy(self):
        ranges = audit.parse_ranges("Foo 2021 – 2022", today=(2026, 10))
        self.assertEqual(len(ranges), 1)
        self.assertTrue(ranges[0]["fuzzy"])

    def test_reversed_range_flagged(self):
        ranges = audit.parse_ranges("Foo 2025.09 – 2024.01", today=(2026, 10))
        result = audit.check_timeline(ranges)
        self.assertTrue(any(f["type"] == "reversed_range" for f in result["findings"]))

    def test_overlap_detected(self):
        text = "A 2024.01 – 至今\nB 2023.06 – 2024.06"
        ranges = audit.parse_ranges(text, today=(2026, 10))
        result = audit.check_timeline(ranges)
        self.assertTrue(any(f["type"] == "overlap" for f in result["findings"]))

    def test_gap_detected(self):
        text = "A 2025.09 – 至今\nB 2023.06 – 2024.06"
        ranges = audit.parse_ranges(text, today=(2026, 10))
        result = audit.check_timeline(ranges)
        gaps = [f for f in result["findings"] if f["type"] == "gap"]
        self.assertEqual(len(gaps), 1)
        self.assertGreaterEqual(gaps[0]["gap_months"], 3)

    def test_clean_timeline_no_findings(self):
        text = "A 2025.09 – 至今\nB 2023.06 – 2025.08"
        ranges = audit.parse_ranges(text, today=(2026, 10))
        result = audit.check_timeline(ranges)
        self.assertEqual(result["findings"], [])


class ReportTest(unittest.TestCase):
    def test_report_sorts_by_risk(self):
        audit_dir = make_audit("Demo 2024.01 – 至今\n")
        ledger = {
            "schema_version": 1,
            "claims": [
                {"id": "c002", "text": "low one", "location": "x",
                 "check_method": "hr_call", "risk": "low",
                 "reason": "r", "fix": "f"},
                {"id": "c001", "text": "high one", "location": "x",
                 "check_method": "reference", "risk": "high",
                 "reason": "r", "fix": "f"},
            ],
        }
        (audit_dir / "audit-ledger.json").write_text(
            json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        out = audit_dir / "report.md"
        self.assertEqual(
            audit.command_report(Namespace(audit_dir=audit_dir, output=out)), 0)
        text = out.read_text(encoding="utf-8")
        self.assertLess(text.index("c001"), text.index("c002"))
        self.assertIn(audit.CLOSING_ZH, text)

    def test_report_rejects_bad_ledger(self):
        audit_dir = make_audit("Demo 2024.01 – 至今\n")
        (audit_dir / "audit-ledger.json").write_text(
            json.dumps({"schema_version": 1, "claims": [
                {"id": "c001", "text": "x"}]}), encoding="utf-8")
        with self.assertRaises(RuntimeError):
            audit.command_report(Namespace(audit_dir=audit_dir, output=None))


if __name__ == "__main__":
    unittest.main()
