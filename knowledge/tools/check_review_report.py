#!/usr/bin/env python3
"""Validate the structure and owner-rule coverage of a Markdown review report."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = (
    "Review scope",
    "Owner rule audit",
    "Public ingress matrix",
    "Producer-consumer trace",
    "Open findings",
    "Completion",
)
MATRIX_SCHEMAS = {
    "Public ingress matrix": (
        "Ingress",
        "Validation/normalization",
        "Before expensive work?",
        "Production-path test/evidence",
    ),
    "Producer-consumer trace": (
        "Value or contract",
        "Producer",
        "Transformations",
        "Final consumer",
        "Stop/failure owner",
        "Evidence",
    ),
}
REQUIRED_AUDITS = {
    "coverage",
    "ingress",
    "producer-consumer",
    "duplication",
    "layering",
    "edge-cases",
    "surface-area",
}
VALID_STATUSES = {
    "PASS",
    "FAIL",
    "MISSING_EVIDENCE",
    "NOT_APPLICABLE",
}
RULE_DEFINITION_RE = re.compile(
    r"\*\*([A-Z][A-Z0-9]*-\d+[a-z]?)"
    r"(?:\s+—|\*\*\s*\|)"
)
REPORT_RULE_ROW_RE = re.compile(
    r"^\|\s*([A-Z][A-Z0-9]*-\d+[a-z]?)\s*\|"
    r"\s*(PASS|FAIL|MISSING_EVIDENCE|NOT_APPLICABLE)\s*\|"
    r"\s*(.*?)\s*\|\s*$"
)
LEGACY_REPORT_ROW_RE = re.compile(
    r"^\|\s*LEGACY:(.+?)#(\d+)\s*\|"
    r"\s*(PASS|FAIL|MISSING_EVIDENCE|NOT_APPLICABLE)\s*\|"
    r"\s*(.*?)\s*\|\s*$"
)
TEMPLATE_PLACEHOLDERS = {
    "<offline/API/chat/internal entry>",
    "<owner and behavior>",
    "<evidence>",
    "<field/behavior>",
    "<source>",
    "<every handoff>",
    "<actual reader>",
    "<boundary>",
}
COVERAGE_FOOTER_RE = re.compile(
    r"^OWNER RULE COVERAGE:\s*(.+?):\s*(\d+)\s*/\s*(\d+)\s+"
    r"stable IDs inventoried\s*—\s*(\d+)\s+pass\s*/\s*"
    r"(\d+)\s+fail\s*/\s*(\d+)\s+missing evidence\s*/\s*"
    r"(\d+)\s+not applicable\s*$",
    re.IGNORECASE | re.MULTILINE,
)
LEGACY_COVERAGE_FOOTER_RE = re.compile(
    r"^OWNER RULE COVERAGE:\s*(.+?):\s*(\d+)\s+source units inventoried\s*"
    r"—\s*(\d+)\s+pass\s*/\s*(\d+)\s+fail\s*/\s*"
    r"(\d+)\s+missing evidence\s*/\s*(\d+)\s+not applicable\s*—\s*"
    r"legacy-unstructured,\s*no exact clause-coverage claim\s*$",
    re.IGNORECASE | re.MULTILINE,
)
AUDITS_FOOTER_RE = re.compile(
    r"^AUDITS RUN:\s*([^—\n]+?)\s*—\s*(\d+)\s+findings?\s*"
    r"\(\s*(\d+)\s+P0\s*,\s*(\d+)\s+P1\s*,\s*(\d+)\s+P2\s*\)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--rules",
        action="append",
        default=[],
        type=Path,
        help="Owner rules.md path. Repeat for multiple owners.",
    )
    parser.add_argument(
        "--legacy-rules",
        action="append",
        default=[],
        type=Path,
        help=(
            "Legacy owner rules path without stable IDs. Repeat for multiple owners."
        ),
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help=(
            "Also fail when an owner rule is FAIL/MISSING_EVIDENCE or the "
            "report contains open findings."
        ),
    )
    return parser.parse_args()


def read_text(path: Path, label: str, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"{label} does not exist: {path}")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label} is not valid UTF-8: {path}")
        return ""


def extract_rule_ids(text: str) -> list[str]:
    return RULE_DEFINITION_RE.findall(text)


def extract_legacy_source_units(text: str) -> list[str]:
    """Count mechanical Markdown source units without claiming clause semantics."""
    units: list[str] = []
    paragraph: list[str] = []
    in_fence = False
    in_frontmatter = text.startswith("---\n")
    table_header_seen = False

    def flush_paragraph() -> None:
        if paragraph:
            units.append(" ".join(paragraph).strip())
            paragraph.clear()

    for line_number, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if in_frontmatter:
            if line_number > 0 and stripped == "---":
                in_frontmatter = False
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            flush_paragraph()
            table_header_seen = False
            continue
        if stripped.startswith("#"):
            flush_paragraph()
            continue
        if re.match(r"^\s*[-*+]\s+", line):
            flush_paragraph()
            units.append(re.sub(r"^\s*[-*+]\s+", "", line).strip())
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            cells = split_markdown_row(stripped)
            if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                table_header_seen = True
                continue
            if not table_header_seen:
                table_header_seen = True
                continue
            units.append(" | ".join(cells))
            continue
        paragraph.append(stripped)
    flush_paragraph()
    return [unit for unit in units if unit]


def normalize_path_label(value: str | Path) -> str:
    return str(value).strip().replace("\\", "/").casefold()


def matching_owner_paths(label: str, paths: list[Path]) -> list[Path]:
    normalized_label = normalize_path_label(label)
    return [
        path
        for path in paths
        if normalize_path_label(path) == normalized_label
        or normalize_path_label(path).endswith(f"/{normalized_label}")
    ]


def extract_section(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else None


def split_markdown_row(line: str) -> list[str]:
    content = line.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []
    code_delimiter_length = 0
    escaped = False
    index = 0
    while index < len(content):
        char = content[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            index += 1
            continue
        if char == "`":
            run_end = index
            while run_end < len(content) and content[run_end] == "`":
                run_end += 1
            run_length = run_end - index
            if code_delimiter_length == 0:
                code_delimiter_length = run_length
            elif code_delimiter_length == run_length:
                code_delimiter_length = 0
            current.append(content[index:run_end])
            index = run_end
            continue
        if char == "|" and code_delimiter_length == 0:
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells


def markdown_table(section: str) -> tuple[list[str], list[list[str]]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_markdown_row(stripped)
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return (rows[0], rows[1:]) if rows else ([], [])


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    report = read_text(args.report, "report", errors)
    if not report:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    sections: dict[str, str] = {}
    for heading in REQUIRED_HEADINGS:
        section = extract_section(report, heading)
        if section is None:
            errors.append(f"missing section: ## {heading}")
        else:
            sections[heading] = section

    expected_ids: list[str] = []
    definition_owner: dict[str, Path] = {}
    rule_ids_by_owner: dict[Path, list[str]] = {}
    for rules_path in args.rules:
        rules_text = read_text(rules_path, "rules file", errors)
        if rules_path.is_file() and not rules_text.strip():
            errors.append(f"rules file is empty: {rules_path}")
        rule_ids = extract_rule_ids(rules_text)
        if rules_text.strip() and not rule_ids:
            errors.append(f"no stable rule IDs found in: {rules_path}")
        rule_ids_by_owner[rules_path] = []
        for rule_id in rule_ids:
            if rule_id in definition_owner:
                errors.append(
                    "duplicate owner rule definition: "
                    f"{rule_id} in {definition_owner[rule_id]} and {rules_path}"
                )
                continue
            definition_owner[rule_id] = rules_path
            expected_ids.append(rule_id)
            rule_ids_by_owner[rules_path].append(rule_id)

    legacy_source_units: dict[Path, list[str]] = {}
    for rules_path in args.legacy_rules:
        rules_text = read_text(rules_path, "legacy rules file", errors)
        if rules_path.is_file() and not rules_text.strip():
            errors.append(f"legacy rules file is empty: {rules_path}")
        stable_ids = extract_rule_ids(rules_text)
        if stable_ids:
            errors.append(
                f"legacy rules file contains stable IDs; use --rules: {rules_path}"
            )
        legacy_source_units[rules_path] = extract_legacy_source_units(rules_text)
        if rules_text.strip() and not legacy_source_units[rules_path]:
            errors.append(f"no legacy source units found in: {rules_path}")

    report_rows: dict[str, list[tuple[str, str]]] = {}
    legacy_report_rows: dict[Path, list[tuple[int, str, str]]] = {
        path: [] for path in args.legacy_rules
    }
    rule_section = sections.get("Owner rule audit", "")
    for line in rule_section.splitlines():
        match = REPORT_RULE_ROW_RE.match(line.strip())
        if not match:
            continue
        rule_id, status, evidence = match.groups()
        report_rows.setdefault(rule_id, []).append((status, evidence.strip()))

    for line in rule_section.splitlines():
        match = LEGACY_REPORT_ROW_RE.match(line.strip())
        if not match:
            continue
        label, unit_number_text, status, evidence = match.groups()
        owner_matches = matching_owner_paths(label.strip(), args.legacy_rules)
        if len(owner_matches) != 1:
            errors.append(
                "legacy audit row label must match exactly one --legacy-rules "
                f"path: {label.strip()}"
            )
            continue
        owner = owner_matches[0]
        legacy_report_rows[owner].append(
            (int(unit_number_text), status, evidence.strip())
        )

    for rule_id in expected_ids:
        rows = report_rows.get(rule_id, [])
        if not rows:
            errors.append(f"missing owner rule row: {rule_id}")
        elif len(rows) > 1:
            errors.append(f"duplicate owner rule row: {rule_id}")

    unexpected = sorted(set(report_rows) - set(expected_ids))
    for rule_id in unexpected:
        errors.append(f"report rule ID is not defined by supplied rules files: {rule_id}")

    for rule_id, rows in report_rows.items():
        for status, evidence in rows:
            if status not in VALID_STATUSES:
                errors.append(f"invalid status for {rule_id}: {status}")
            if not evidence or evidence in {"-", "N/A"}:
                errors.append(f"missing evidence for owner rule row: {rule_id}")
            if args.require_clean and status in {"FAIL", "MISSING_EVIDENCE"}:
                errors.append(f"review is not clean: {rule_id} is {status}")

    for owner, rows in legacy_report_rows.items():
        if not rows:
            errors.append(f"legacy owner audit has no source-unit row: {owner}")
            continue
        unit_numbers = [unit_number for unit_number, _, _ in rows]
        if len(unit_numbers) != len(set(unit_numbers)):
            errors.append(f"duplicate legacy source-unit number for: {owner}")
        if sorted(unit_numbers) != list(range(1, len(unit_numbers) + 1)):
            errors.append(f"legacy source-unit numbers must be contiguous from 1: {owner}")
        expected_unit_count = len(legacy_source_units.get(owner, []))
        if len(rows) != expected_unit_count:
            errors.append(
                f"legacy source-unit row count for {owner} does not match file: "
                f"report={len(rows)}, expected={expected_unit_count}"
            )
        for unit_number, status, evidence in rows:
            if not evidence or evidence in {"-", "N/A"}:
                errors.append(
                    f"missing evidence for legacy source unit {owner}#{unit_number}"
                )
            if args.require_clean and status in {"FAIL", "MISSING_EVIDENCE"}:
                errors.append(
                    f"review is not clean: {owner}#{unit_number} is {status}"
                )

    if not args.rules and not args.legacy_rules and "OWNER RULES: none" not in rule_section:
        errors.append(
            "no --rules supplied; Owner rule audit must contain 'OWNER RULES: none'"
        )

    for heading, expected_header in MATRIX_SCHEMAS.items():
        section = sections.get(heading)
        if section is None:
            continue
        header, data_rows = markdown_table(section)
        if tuple(header) != expected_header:
            errors.append(
                f"{heading} header must be: {' | '.join(expected_header)}"
            )
        if not data_rows:
            errors.append(f"{heading} has no Markdown data row")
            continue
        for row_number, row in enumerate(data_rows, start=1):
            if len(row) != len(expected_header):
                errors.append(
                    f"{heading} row {row_number} has {len(row)} cells; "
                    f"expected {len(expected_header)}"
                )
                continue
            for column_number, cell in enumerate(row, start=1):
                if not cell:
                    errors.append(
                        f"{heading} row {row_number} column {column_number} is empty"
                    )
                elif cell in TEMPLATE_PLACEHOLDERS:
                    errors.append(
                        f"{heading} row {row_number} column {column_number} "
                        "still contains a template placeholder"
                    )

    completion = sections.get("Completion", "")
    if "OWNER RULE COVERAGE:" not in completion:
        errors.append("Completion is missing OWNER RULE COVERAGE footer")
    if "AUDITS RUN:" not in completion:
        errors.append("Completion is missing AUDITS RUN footer")
    stable_coverage_matches = list(COVERAGE_FOOTER_RE.finditer(completion))
    legacy_coverage_matches = list(LEGACY_COVERAGE_FOOTER_RE.finditer(completion))
    raw_coverage_footer_count = len(
        re.findall(r"^OWNER RULE COVERAGE:", completion, re.MULTILINE)
    )
    if raw_coverage_footer_count != len(stable_coverage_matches) + len(
        legacy_coverage_matches
    ):
        errors.append("Completion contains an unparseable OWNER RULE COVERAGE footer")
    matched_stable_owners: set[Path] = set()
    for match in stable_coverage_matches:
        label = match.group(1).strip()
        inventoried, total, passed, failed, missing, not_applicable = map(
            int, match.groups()[1:]
        )
        if not args.rules and not args.legacy_rules and label.casefold() == "none":
            owner_ids: list[str] = []
        else:
            owner_matches = matching_owner_paths(label, list(rule_ids_by_owner))
            if len(owner_matches) != 1:
                errors.append(
                    "Completion owner coverage label must match exactly one "
                    f"--rules path: {label}"
                )
                continue
            owner = owner_matches[0]
            if owner in matched_stable_owners:
                errors.append(f"duplicate owner coverage footer: {label}")
                continue
            matched_stable_owners.add(owner)
            owner_ids = rule_ids_by_owner[owner]

        actual_status_counts = {
            status: sum(
                report_rows[rule_id][0][0] == status
                for rule_id in owner_ids
                if len(report_rows.get(rule_id, [])) == 1
            )
            for status in VALID_STATUSES
        }
        expected_total = len(owner_ids)
        if (inventoried, total) != (expected_total, expected_total):
            errors.append(
                f"Completion owner coverage total for {label} does not match rules: "
                f"footer={inventoried}/{total}, expected={expected_total}/{expected_total}"
            )
        footer_status_counts = {
            "PASS": passed,
            "FAIL": failed,
            "MISSING_EVIDENCE": missing,
            "NOT_APPLICABLE": not_applicable,
        }
        if footer_status_counts != actual_status_counts:
            errors.append(
                f"Completion owner coverage status counts for {label} do not "
                f"match audit rows: footer={footer_status_counts}, "
                f"body={actual_status_counts}"
            )

    missing_stable_footers = set(rule_ids_by_owner) - matched_stable_owners
    for path in sorted(missing_stable_footers, key=str):
        errors.append(f"Completion is missing owner coverage footer for: {path}")

    matched_legacy_owners: set[Path] = set()
    for match in legacy_coverage_matches:
        label = match.group(1).strip()
        inventoried, passed, failed, missing, not_applicable = map(
            int, match.groups()[1:]
        )
        owner_matches = matching_owner_paths(label, args.legacy_rules)
        if len(owner_matches) != 1:
            errors.append(
                "Completion legacy coverage label must match exactly one "
                f"--legacy-rules path: {label}"
            )
            continue
        owner = owner_matches[0]
        if owner in matched_legacy_owners:
            errors.append(f"duplicate legacy owner coverage footer: {label}")
            continue
        matched_legacy_owners.add(owner)
        rows = legacy_report_rows.get(owner, [])
        footer_status_counts = {
            "PASS": passed,
            "FAIL": failed,
            "MISSING_EVIDENCE": missing,
            "NOT_APPLICABLE": not_applicable,
        }
        actual_status_counts = {
            status: sum(row_status == status for _, row_status, _ in rows)
            for status in VALID_STATUSES
        }
        expected_unit_count = len(legacy_source_units.get(owner, []))
        if inventoried != expected_unit_count:
            errors.append(
                f"Completion legacy coverage total for {label} does not match "
                f"rules file: footer={inventoried}, expected={expected_unit_count}"
            )
        if footer_status_counts != actual_status_counts:
            errors.append(
                f"Completion legacy coverage status counts for {label} do not "
                f"match audit rows: footer={footer_status_counts}, "
                f"body={actual_status_counts}"
            )
    for path in sorted(set(args.legacy_rules) - matched_legacy_owners, key=str):
        errors.append(f"Completion is missing legacy coverage footer for: {path}")

    expected_coverage_lines = (
        len(args.rules) + len(args.legacy_rules)
        if args.rules or args.legacy_rules
        else 1
    )
    if len(stable_coverage_matches) + len(legacy_coverage_matches) != expected_coverage_lines:
        errors.append(
            "Completion must contain exactly one owner coverage footer per owner"
        )

    audits_matches = list(AUDITS_FOOTER_RE.finditer(completion))
    raw_audits_footer_count = len(re.findall(r"^AUDITS RUN:", completion, re.MULTILINE))
    if raw_audits_footer_count != len(audits_matches):
        errors.append("Completion contains an unparseable AUDITS RUN footer")
    if len(audits_matches) != 1:
        errors.append("Completion must contain exactly one machine-readable AUDITS RUN footer")
    else:
        audits_match = audits_matches[0]
        reported_audits = {
            audit.strip().lower()
            for audit in audits_match.group(1).split(",")
            if audit.strip()
        }
        missing_audits = sorted(REQUIRED_AUDITS - reported_audits)
        if missing_audits:
            errors.append(
                "Completion AUDITS RUN footer is missing: "
                + ", ".join(missing_audits)
            )
        footer_total, footer_p0, footer_p1, footer_p2 = map(
            int, audits_match.groups()[1:]
        )
        footer_counts = (footer_p0, footer_p1, footer_p2)
        if footer_total != sum(footer_counts):
            errors.append(
                "Completion finding total does not equal its P0/P1/P2 counts"
            )
        open_findings = sections.get("Open findings", "")
        actual_counts = tuple(
            len(re.findall(rf"^\s*[-*]\s+(?:\*\*)?P{priority}\b", open_findings, re.MULTILINE))
            for priority in range(3)
        )
        if actual_counts != footer_counts:
            errors.append(
                "Open findings do not match Completion P0/P1/P2 counts: "
                f"body={actual_counts}, footer={footer_counts}"
            )
        if footer_total == 0 and not re.search(
            r"^\s*[-*]\s+(?:\*\*)?none\b", open_findings, re.MULTILINE | re.IGNORECASE
        ):
            errors.append("Open findings must contain an explicit 'none' when count is zero")
        if args.require_clean and footer_total != 0:
            errors.append(
                "review is not clean: Completion reports "
                f"{footer_total} open finding(s)"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Review report incomplete: {len(errors)} error(s).", file=sys.stderr)
        return 1

    fail_count = sum(
        status == "FAIL" for rows in report_rows.values() for status, _ in rows
    ) + sum(
        status == "FAIL"
        for rows in legacy_report_rows.values()
        for _, status, _ in rows
    )
    missing_count = sum(
        status == "MISSING_EVIDENCE"
        for rows in report_rows.values()
        for status, _ in rows
    ) + sum(
        status == "MISSING_EVIDENCE"
        for rows in legacy_report_rows.values()
        for _, status, _ in rows
    )
    print(
        "Review report structure complete: "
        f"{len(report_rows)} stable rule row(s), "
        f"{sum(len(rows) for rows in legacy_report_rows.values())} legacy source unit(s), "
        f"{fail_count} FAIL, "
        f"{missing_count} MISSING_EVIDENCE."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
