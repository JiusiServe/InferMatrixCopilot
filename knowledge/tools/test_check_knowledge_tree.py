#!/usr/bin/env python3
"""Tests for deterministic knowledge-tree ownership checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import check_knowledge_tree


class OwnerAxisTests(unittest.TestCase):
    def test_sibling_workflow_and_source_owners_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "demo"
            (repo / "dev").mkdir(parents=True)
            (repo / "components" / "configuration" / "guides").mkdir(parents=True)
            (repo / "models" / "demo-model" / "incidents").mkdir(parents=True)

            self.assertEqual(check_knowledge_tree.owner_axis_violations(repo), [])

    def test_source_owner_nested_below_workflow_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "demo"
            (repo / "dev" / "components" / "configuration").mkdir(parents=True)

            violations = check_knowledge_tree.owner_axis_violations(repo)

            self.assertEqual(len(violations), 1)
            self.assertIn("源码 owner 目录必须直属仓库", violations[0])

class ExactDuplicateTests(unittest.TestCase):
    def test_identical_page_body_across_owners_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "dev" / "rules.md"
            second = root / "components" / "configuration" / "rules.md"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            body = "# Rules\n\n" + ("This owner-specific rule must not be copied.\n" * 8)
            first.write_text(body, encoding="utf-8")
            second.write_text(body, encoding="utf-8")

            violations = check_knowledge_tree.exact_page_duplicate_violations(
                [first, second]
            )

            self.assertEqual(len(violations), 1)
            self.assertIn("整页正文在多个 owner 下完全重复", violations[0])

    def test_different_pages_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "dev" / "rules.md"
            second = root / "components" / "configuration" / "rules.md"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text("# Dev\n\n" + ("workflow rule\n" * 20), encoding="utf-8")
            second.write_text(
                "# Configuration\n\n" + ("source owner rule\n" * 20),
                encoding="utf-8",
            )

            self.assertEqual(
                check_knowledge_tree.exact_page_duplicate_violations([first, second]),
                [],
            )


if __name__ == "__main__":
    unittest.main()
