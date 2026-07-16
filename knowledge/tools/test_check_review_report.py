from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import check_review_report


VALID_REPORT = """# Review report

## Review scope
- Base SHA: abc
- Diff: abc -> working tree
- Owners: rules.md
- In-scope untracked files: none

## Owner rule audit
| Rule ID | Status | Evidence |
|---|---|---|
| DEMO-1a | PASS | src.py:run + test_run |
| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API |

## Public ingress matrix
| Ingress | Validation/normalization | Before expensive work? | Production-path test/evidence |
|---|---|---|---|
| CLI | parser | yes | test_cli |

## Producer-consumer trace
| Value or contract | Producer | Transformations | Final consumer | Stop/failure owner | Evidence |
|---|---|---|---|---|---|
| size | CLI | config | model | parser | test_cli |

## Open findings
- none

## Completion
OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable
AUDITS RUN: coverage,ingress,producer-consumer,duplication,layering,edge-cases,surface-area — 0 findings (0 P0, 0 P1, 0 P2)
"""


class ReviewReportCheckerTest(unittest.TestCase):
    def run_checker(
        self,
        report: str,
        rules: str | dict[str, str],
        *,
        legacy_rules: dict[str, str] | None = None,
        require_clean: bool = False,
    ) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "review.md"
            report_path.write_text(report, encoding="utf-8")
            output = io.StringIO()
            argv = ["check_review_report.py", "--report", str(report_path)]
            stable_files = {"rules.md": rules} if isinstance(rules, str) else rules
            for filename, content in stable_files.items():
                rules_path = root / filename
                rules_path.write_text(content, encoding="utf-8")
                argv.extend(["--rules", str(rules_path)])
            for filename, content in (legacy_rules or {}).items():
                rules_path = root / filename
                rules_path.write_text(content, encoding="utf-8")
                argv.extend(["--legacy-rules", str(rules_path)])
            if require_clean:
                argv.append("--require-clean")
            with (
                mock.patch.object(sys, "argv", argv),
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(output),
            ):
                return check_review_report.main(), output.getvalue()

    def test_complete_report_passes(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n\n| **DEMO-1b** | second rule |\n"""
        return_code, output = self.run_checker(VALID_REPORT, rules)
        self.assertEqual(return_code, 0, output)
        self.assertIn("2 stable rule row(s)", output)

    def test_missing_rule_row_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API |\n",
            "",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing owner rule row: DEMO-1b", output)

    def test_template_placeholder_matrix_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace("| CLI | parser | yes | test_cli |", "| <entry> | <validation> | <timing> | <evidence> |")
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("template placeholder", output)

    def test_require_clean_rejects_open_findings(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "— 0 findings (0 P0, 0 P1, 0 P2)",
            "— 1 finding (0 P0, 1 P1, 0 P2)",
        ).replace("- none", "- P1 — production path bypasses validation")
        return_code, output = self.run_checker(
            report, rules, require_clean=True
        )
        self.assertEqual(return_code, 1)
        self.assertIn("1 open finding", output)

    def test_duplicate_rule_definition_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1a — duplicate rule.**\n- **DEMO-1b — second rule.**\n"""
        return_code, output = self.run_checker(VALID_REPORT, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("duplicate owner rule definition: DEMO-1a", output)

    def test_empty_rules_file_fails(self) -> None:
        return_code, output = self.run_checker(VALID_REPORT, "")
        self.assertEqual(return_code, 1)
        self.assertIn("rules file is empty", output)

    def test_stale_zero_finding_footer_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "- none", "- P1 — production path bypasses validation"
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("Open findings do not match", output)

    def test_footer_total_must_equal_priority_counts(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "— 0 findings (0 P0, 0 P1, 0 P2)",
            "— 2 findings (0 P0, 1 P1, 0 P2)",
        ).replace("- none", "- P1 — one real finding")
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("finding total does not equal", output)

    def test_markdown_escaped_pipe_and_angle_brackets_pass(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | parser | yes | test_cli |",
            r"| CLI | accepts A \| B | yes | `List<int>` in test_cli |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 0, output)

    def test_multi_backtick_code_span_with_pipe_passes(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | parser | yes | test_cli |",
            "| CLI | ``accepts `A | B` literally`` | yes | test_cli |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 0, output)

    def test_unparseable_completion_footer_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "OWNER RULE COVERAGE: nonsense",
        ).replace(
            "AUDITS RUN: coverage,ingress,producer-consumer,duplication,layering,edge-cases,surface-area",
            "AUDITS RUN: nothing",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing owner coverage footer", output)
        self.assertIn("AUDITS RUN footer is missing", output)

    def test_coverage_footer_counts_must_match_rows(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "1/2 stable IDs inventoried — 2 pass / 0 fail / 0 missing evidence / 0 not applicable",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("owner coverage total for rules.md does not match", output)
        self.assertIn("status counts for rules.md do not match", output)

    def test_multiple_stable_and_legacy_owners_pass(self) -> None:
        stable_rules = {
            "rules.md": "- **DEMO-1a — first rule.**\n",
            "other-rules.md": "- **OTHER-1a — other owner rule.**\n",
        }
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API |",
            "| OTHER-1a | NOT_APPLICABLE | diff does not touch the other owner |\n"
            "| LEGACY:legacy.md#1 | PASS | quoted old rule + src.py:run |",
        ).replace(
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "OWNER RULE COVERAGE: rules.md: 1/1 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable\n"
            "OWNER RULE COVERAGE: other-rules.md: 1/1 stable IDs inventoried — 0 pass / 0 fail / 0 missing evidence / 1 not applicable\n"
            "OWNER RULE COVERAGE: legacy.md: 1 source units inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim",
        )
        return_code, output = self.run_checker(
            report,
            stable_rules,
            legacy_rules={"legacy.md": "- Old rule without a stable ID.\n"},
        )
        self.assertEqual(return_code, 0, output)

    def test_duplicate_audits_footer_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        audit_line = (
            "AUDITS RUN: coverage,ingress,producer-consumer,duplication,"
            "layering,edge-cases,surface-area — 0 findings (0 P0, 0 P1, 0 P2)"
        )
        report = VALID_REPORT.replace(audit_line, f"{audit_line}\n{audit_line}")
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("exactly one machine-readable AUDITS RUN footer", output)

    def test_legacy_owner_without_source_unit_row_fails(self) -> None:
        stable_rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "AUDITS RUN:",
            "OWNER RULE COVERAGE: legacy.md: 0 source units inventoried — 0 pass / 0 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim\nAUDITS RUN:",
        )
        return_code, output = self.run_checker(
            report,
            stable_rules,
            legacy_rules={"legacy.md": "- Old rule without a stable ID.\n"},
        )
        self.assertEqual(return_code, 1)
        self.assertIn("legacy owner audit has no source-unit row", output)

    def test_unparseable_extra_footer_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "AUDITS RUN:", "AUDITS RUN: contradictory\nAUDITS RUN:"
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("unparseable AUDITS RUN footer", output)

    def test_legacy_report_must_cover_every_mechanical_source_unit(self) -> None:
        stable_rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API |",
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API |\n"
            "| LEGACY:legacy.md#1 | PASS | quoted first old rule + src.py:run |",
        ).replace(
            "AUDITS RUN:",
            "OWNER RULE COVERAGE: legacy.md: 1 source units inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim\nAUDITS RUN:",
        )
        return_code, output = self.run_checker(
            report,
            stable_rules,
            legacy_rules={
                "legacy.md": "- First old rule.\n- Second old rule.\n"
            },
        )
        self.assertEqual(return_code, 1)
        self.assertIn("legacy source-unit row count", output)
        self.assertIn("expected=2", output)

    def test_success_summary_counts_legacy_failures(self) -> None:
        stable_rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API |",
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API |\n"
            "| LEGACY:legacy.md#1 | FAIL | quoted old rule + broken src.py:run |",
        ).replace(
            "AUDITS RUN:",
            "OWNER RULE COVERAGE: legacy.md: 1 source units inventoried — 0 pass / 1 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim\nAUDITS RUN:",
        )
        return_code, output = self.run_checker(
            report,
            stable_rules,
            legacy_rules={"legacy.md": "- Old rule.\n"},
        )
        self.assertEqual(return_code, 0, output)
        self.assertIn("1 FAIL", output)


if __name__ == "__main__":
    unittest.main()
