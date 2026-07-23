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
| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| DEMO-1a | PASS | src.py:run + test_run | - |
| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |

## Public ingress matrix
| Ingress | Actual dispatcher | Contract check | First expensive operation | Owner adapter/consumer | Production-path test/evidence |
|---|---|---|---|---|---|
| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |

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

VALID_FINDING = (
    "DIFF:src.py:run changes validation; "
    "PATH:cli.main -> model.run; "
    "CONTRACT:src.py:validate previously rejects bad input; "
    "FAILURE:invalid input reaches model.load and fails after allocation; "
    "COUNTEREVIDENCE:checked the canonical direct caller and no alternate guard exists; "
    "FIX:restore the owner validation before model.load"
)

GROUPED_RULES = """# Demo rules

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | every review | `DEMO-1a` |
| `api` | public API changes | `DEMO-1b` |

- **DEMO-1a — first rule.**
- **DEMO-1b — second rule.**
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
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n",
            "",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing owner rule row: DEMO-1b", output)

    def test_template_placeholder_matrix_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| <offline/API/chat/internal entry> | <real function reached from the public entry> | <validation/normalization and location> | <decode/load/GPU/VAE call> | <actual adapter or bypass> | <evidence> |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("template placeholder", output)

    def test_require_clean_rejects_open_findings(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "— 0 findings (0 P0, 0 P1, 0 P2)",
            "— 1 finding (0 P0, 1 P1, 0 P2)",
        ).replace(
            "- none",
            "- P1 F1 OWNER_RULE:NONE — production path bypasses validation",
        )
        return_code, output = self.run_checker(report, rules, require_clean=True)
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
            "- none",
            "- P1 F1 OWNER_RULE:NONE — production path bypasses validation",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("Open findings do not match", output)

    def test_footer_total_must_equal_priority_counts(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "— 0 findings (0 P0, 0 P1, 0 P2)",
            "— 2 findings (0 P0, 1 P1, 0 P2)",
        ).replace(
            "- none",
            "- P1 F1 OWNER_RULE:NONE — one real finding with a concrete fix",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("finding total does not equal", output)

    def test_markdown_escaped_pipe_and_angle_brackets_pass(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            r"| CLI | `cli.main` | accepts A \| B | `model.load` | `model.run` | `List<int>` in test_cli |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 0, output)

    def test_multi_backtick_code_span_with_pipe_passes(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| CLI | `cli.main` | ``accepts `A | B` literally`` | `model.load` | `model.run` | test_cli |",
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

    def test_fail_row_requires_finding_mapping(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1a | PASS | src.py:run + test_run | - |",
            "| DEMO-1a | FAIL | src.py:run is broken | - |",
        ).replace(
            "1 pass / 0 fail",
            "0 pass / 1 fail",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("FAIL row must map to FINDING", output)

    def test_fail_mapping_must_reference_existing_finding(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1a | PASS | src.py:run + test_run | - |",
            "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F9 |",
        ).replace(
            "1 pass / 0 fail",
            "0 pass / 1 fail",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("references missing finding: F9", output)

    def test_fail_mapping_to_finding_passes(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace(
                "1 pass / 0 fail",
                "0 pass / 1 fail",
            )
            .replace(
                "- none",
                f"- P1 F1 — {VALID_FINDING}",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 0, output)

    def test_finding_requires_all_proof_labels(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace("1 pass / 0 fail", "0 pass / 1 fail")
            .replace(
                "- none",
                "- P1 F1 — DIFF:src.py changed; FAILURE:request crashes; FIX:restore guard",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing proof label(s)", output)
        self.assertIn("COUNTEREVIDENCE", output)

    def test_finding_proof_labels_require_real_values(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace("1 pass / 0 fail", "0 pass / 1 fail")
            .replace(
                "- none",
                "- P1 F1 — DIFF:none; PATH:none; CONTRACT:none; "
                "FAILURE:none; COUNTEREVIDENCE:none; FIX:none",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("empty proof value(s)", output)

    def test_investigation_note_does_not_count_as_finding(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "- none",
            "- none\n- NOTE N1 — a possible architecture improvement needs investigation",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 0, output)

    def test_grouped_owner_can_audit_core_only(self) -> None:
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n",
            "",
        ).replace(
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "OWNER RULE GROUPS: rules.md: core\n"
            "OWNER RULE COVERAGE: rules.md: 1/1 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable",
        )
        return_code, output = self.run_checker(report, GROUPED_RULES)
        self.assertEqual(return_code, 0, output)
        self.assertIn("1 stable rule row(s)", output)

    def test_grouped_owner_can_select_multiple_groups(self) -> None:
        report = VALID_REPORT.replace(
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "OWNER RULE GROUPS: rules.md: core,api\n"
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
        )
        return_code, output = self.run_checker(report, GROUPED_RULES)
        self.assertEqual(return_code, 0, output)

    def test_grouped_owner_requires_selection_footer(self) -> None:
        return_code, output = self.run_checker(VALID_REPORT, GROUPED_RULES)
        self.assertEqual(return_code, 1)
        self.assertIn("missing OWNER RULE GROUPS footer", output)

    def test_group_selection_must_include_core(self) -> None:
        report = VALID_REPORT.replace(
            "| DEMO-1a | PASS | src.py:run + test_run | - |\n",
            "",
        ).replace(
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "OWNER RULE GROUPS: rules.md: api\n"
            "OWNER RULE COVERAGE: rules.md: 1/1 stable IDs inventoried — 0 pass / 0 fail / 0 missing evidence / 1 not applicable",
        )
        return_code, output = self.run_checker(report, GROUPED_RULES)
        self.assertEqual(return_code, 1)
        self.assertIn("must include core", output)

    def test_unknown_rule_group_fails(self) -> None:
        report = VALID_REPORT.replace(
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "OWNER RULE GROUPS: rules.md: core,unknown\n"
            "OWNER RULE COVERAGE: rules.md: 1/1 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable",
        ).replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n",
            "",
        )
        return_code, output = self.run_checker(report, GROUPED_RULES)
        self.assertEqual(return_code, 1)
        self.assertIn("unknown group", output)

    def test_grouped_rules_must_assign_every_stable_id(self) -> None:
        rules = GROUPED_RULES.replace(
            "| `api` | public API changes | `DEMO-1b` |\n",
            "",
        )
        report = VALID_REPORT.replace(
            "OWNER RULE COVERAGE: rules.md: 2/2 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 1 not applicable",
            "OWNER RULE GROUPS: rules.md: core\n"
            "OWNER RULE COVERAGE: rules.md: 1/1 stable IDs inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable",
        ).replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n",
            "",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("leaves stable IDs ungrouped", output)

    def test_review_group_name_must_be_machine_readable(self) -> None:
        rules = GROUPED_RULES.replace("| `core` |", "| `核心` |")
        return_code, output = self.run_checker(VALID_REPORT, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("review group name must use lowercase", output)

    def test_missing_evidence_can_map_to_specific_draft_blocker(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1a | PASS | src.py:run + test_run | - |",
            "| DEMO-1a | MISSING_EVIDENCE | target test cannot collect | DRAFT:missing vllm runtime |",
        ).replace(
            "1 pass / 0 fail / 0 missing evidence",
            "0 pass / 0 fail / 1 missing evidence",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 0, output)

    def test_open_finding_requires_unique_id(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "- none",
            "- P1 — production path bypasses validation",
        ).replace(
            "— 0 findings (0 P0, 0 P1, 0 P2)",
            "— 1 finding (0 P0, 1 P1, 0 P2)",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("unique F<number>", output)

    def test_fenced_finding_does_not_satisfy_mapping(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace(
                "1 pass / 0 fail",
                "0 pass / 1 fail",
            )
            .replace(
                "- none",
                "```markdown\n- P1 F1 — hidden fake finding with no visible fix\n```",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("references missing finding: F1", output)

    def test_commented_owner_table_does_not_count(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        table = """| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| DEMO-1a | PASS | src.py:run + test_run | - |
| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |"""
        report = VALID_REPORT.replace(table, f"<!--\n{table}\n-->")
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing owner rule row: DEMO-1a", output)

    def test_ingress_sentinel_cells_fail(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| CLI | - | - | - | - | evidence |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("contains a sentinel", output)

    def test_legacy_invalid_status_fails_require_clean(self) -> None:
        stable_rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |",
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n"
            "| LEGACY:legacy.md#1 | BOGUS | quoted old rule + src.py:run | - |",
        ).replace(
            "AUDITS RUN:",
            "OWNER RULE COVERAGE: legacy.md: 1 source units inventoried — 0 pass / 0 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim\nAUDITS RUN:",
        )
        return_code, output = self.run_checker(
            report,
            stable_rules,
            legacy_rules={"legacy.md": "- Old rule.\n"},
            require_clean=True,
        )
        self.assertEqual(return_code, 1)
        self.assertIn("invalid status for legacy source unit", output)

    def test_unmapped_finding_requires_owner_rule_none(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "- none",
            "- P1 F1 — independent concrete issue with a smallest safe fix",
        ).replace(
            "— 0 findings (0 P0, 0 P1, 0 P2)",
            "— 1 finding (0 P0, 1 P1, 0 P2)",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("is not referenced by an owner rule", output)

    def test_emptyish_draft_blocker_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1a | PASS | src.py:run + test_run | - |",
            "| DEMO-1a | MISSING_EVIDENCE | target test cannot collect | DRAFT:- |",
        ).replace(
            "1 pass / 0 fail / 0 missing evidence",
            "0 pass / 0 fail / 1 missing evidence",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("DRAFT:<specific blocker>", output)

    def test_bare_finding_body_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace(
                "1 pass / 0 fail",
                "0 pass / 1 fail",
            )
            .replace(
                "- none",
                "- P1 F1",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("substantive failure", output)

    def test_duplicate_required_heading_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "## Review scope",
            "## Review scope\n\nDuplicate body\n\n## Review scope",
            1,
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("duplicate section: ## Review scope", output)

    def test_closing_hash_duplicate_heading_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "## Review scope",
            "## Review scope ##\n\nDuplicate body\n\n## Review scope",
            1,
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("duplicate section: ## Review scope", output)

    def test_indented_owner_table_does_not_count(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        table = """| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| DEMO-1a | PASS | src.py:run + test_run | - |
| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |"""
        indented = "\n".join(f"    {line}" for line in table.splitlines())
        report = VALID_REPORT.replace(table, indented)
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing owner rule row: DEMO-1a", output)

    def test_hidden_div_owner_table_does_not_count(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        table = """| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| DEMO-1a | PASS | src.py:run + test_run | - |
| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |"""
        report = VALID_REPORT.replace(table, f"<div hidden>\n{table}\n</div>")
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing owner rule row: DEMO-1a", output)

    def test_hidden_section_and_unclosed_comment_do_not_count(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        table = """| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| DEMO-1a | PASS | src.py:run + test_run | - |
| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |"""
        for hidden in (
            f"<section hidden>\n{table}\n</section>",
            f"<!-- unclosed comment\n{table}",
        ):
            with self.subTest(hidden=hidden.splitlines()[0]):
                report = VALID_REPORT.replace(table, hidden)
                return_code, output = self.run_checker(report, rules)
                self.assertEqual(return_code, 1)
                self.assertIn("missing owner rule row: DEMO-1a", output)

    def test_indented_finding_does_not_satisfy_mapping(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace(
                "1 pass / 0 fail",
                "0 pass / 1 fail",
            )
            .replace(
                "- none",
                "    - P1 F1 — hidden fake finding with no visible fix",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("references missing finding: F1", output)

    def test_shorter_fence_does_not_expose_hidden_audit(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        table = """| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| DEMO-1a | PASS | src.py:run + test_run | - |
| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |"""
        report = VALID_REPORT.replace(table, f"````markdown\n```\n{table}\n````")
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("missing owner rule row: DEMO-1a", output)

    def test_markdown_wrapped_matrix_sentinels_fail(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| CLI | `-` | **none** | `unknown` | _tbd_ | evidence |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("contains a sentinel", output)

    def test_placeholder_suffix_is_not_a_concrete_code_path(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| CLI | `- placeholder` | parser before load | `unknown operation` | `none consumer` | test_cli |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("must name a concrete code path", output)

    def test_bare_na_with_evidence_matrix_row_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| N/A-with-evidence | N/A-with-evidence | N/A-with-evidence | N/A-with-evidence | N/A-with-evidence | N/A-with-evidence |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("contains a sentinel", output)

    def test_concrete_na_with_evidence_matrix_row_passes(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| N/A-with-evidence: documentation-only diff has no runtime ingress | no runtime dispatcher exists for this page | no request contract is changed | no expensive operation exists in this diff | documentation renderer is the final consumer | git diff proves only explanatory prose changed |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 0, output)

    def test_na_with_garbage_middle_columns_fails(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| CLI | `cli.main` | parser before load | `model.load` | `model.run` | test_cli |",
            "| N/A-with-evidence: documentation-only diff has no runtime ingress | x | x | x | x | concrete production evidence proves no runtime surface changed |",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("concrete reason in every column", output)

    def test_ordered_legacy_items_are_separate_source_units(self) -> None:
        stable_rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |",
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n"
            "| LEGACY:legacy.md#1 | PASS | quoted first old rule + src.py:run | - |",
        ).replace(
            "AUDITS RUN:",
            "OWNER RULE COVERAGE: legacy.md: 1 source units inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim\nAUDITS RUN:",
        )
        return_code, output = self.run_checker(
            report,
            stable_rules,
            legacy_rules={"legacy.md": "1. First rule.\n2) Second rule.\n"},
        )
        self.assertEqual(return_code, 1)
        self.assertIn("expected=2", output)

    def test_mapped_finding_cannot_declare_owner_rule_none(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace(
                "1 pass / 0 fail",
                "0 pass / 1 fail",
            )
            .replace(
                "- none",
                "- P1 F1 OWNER_RULE:NONE — mapped failure with concrete smallest fix",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("cannot also declare OWNER_RULE:NONE", output)

    def test_misplaced_owner_rule_none_does_not_waive_mapping(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = VALID_REPORT.replace(
            "- none",
            "- P1 F1 — concrete issue and smallest fix OWNER_RULE:NONE",
        ).replace(
            "— 0 findings (0 P0, 0 P1, 0 P2)",
            "— 1 finding (0 P0, 1 P1, 0 P2)",
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("outside the structured position", output)

    def test_finding_id_suffix_does_not_satisfy_mapping(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1a | PASS | src.py:run + test_run | - |",
                "| DEMO-1a | FAIL | src.py:run is broken | FINDING:F1 |",
            )
            .replace(
                "1 pass / 0 fail",
                "0 pass / 1 fail",
            )
            .replace(
                "- none",
                "- P1 F1suffix — concrete issue and smallest safe fix",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
        )
        return_code, output = self.run_checker(report, rules)
        self.assertEqual(return_code, 1)
        self.assertIn("references missing finding: F1", output)

    def test_gibberish_and_punctuation_draft_blockers_fail(self) -> None:
        rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        for draft in (
            "abcdefghijkl",
            "------------",
            "testxxxxxxxx",
            "test test test",
        ):
            with self.subTest(draft=draft):
                report = VALID_REPORT.replace(
                    "| DEMO-1a | PASS | src.py:run + test_run | - |",
                    "| DEMO-1a | MISSING_EVIDENCE | target test cannot collect | "
                    f"DRAFT:{draft} |",
                ).replace(
                    "1 pass / 0 fail / 0 missing evidence",
                    "0 pass / 0 fail / 1 missing evidence",
                )
                return_code, output = self.run_checker(report, rules)
                self.assertEqual(return_code, 1)
                self.assertIn("DRAFT:<specific blocker>", output)

    def test_multiple_stable_and_legacy_owners_pass(self) -> None:
        stable_rules = {
            "rules.md": "- **DEMO-1a — first rule.**\n",
            "other-rules.md": "- **OTHER-1a — other owner rule.**\n",
        }
        report = VALID_REPORT.replace(
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |",
            "| OTHER-1a | NOT_APPLICABLE | diff does not touch the other owner | - |\n"
            "| LEGACY:legacy.md#1 | PASS | quoted old rule + src.py:run | - |",
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
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |",
            "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n"
            "| LEGACY:legacy.md#1 | PASS | quoted first old rule + src.py:run | - |",
        ).replace(
            "AUDITS RUN:",
            "OWNER RULE COVERAGE: legacy.md: 1 source units inventoried — 1 pass / 0 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim\nAUDITS RUN:",
        )
        return_code, output = self.run_checker(
            report,
            stable_rules,
            legacy_rules={"legacy.md": "- First old rule.\n- Second old rule.\n"},
        )
        self.assertEqual(return_code, 1)
        self.assertIn("legacy source-unit row count", output)
        self.assertIn("expected=2", output)

    def test_success_summary_counts_legacy_failures(self) -> None:
        stable_rules = """- **DEMO-1a — first rule.**\n- **DEMO-1b — second rule.**\n"""
        report = (
            VALID_REPORT.replace(
                "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |",
                "| DEMO-1b | NOT_APPLICABLE | diff does not touch the public API | - |\n"
                "| LEGACY:legacy.md#1 | FAIL | quoted old rule + broken src.py:run | FINDING:F1 |",
            )
            .replace(
                "AUDITS RUN:",
                "OWNER RULE COVERAGE: legacy.md: 1 source units inventoried — 0 pass / 1 fail / 0 missing evidence / 0 not applicable — legacy-unstructured, no exact clause-coverage claim\nAUDITS RUN:",
            )
            .replace(
                "- none",
                f"- P1 F1 — {VALID_FINDING}",
            )
            .replace(
                "— 0 findings (0 P0, 0 P1, 0 P2)",
                "— 1 finding (0 P0, 1 P1, 0 P2)",
            )
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
