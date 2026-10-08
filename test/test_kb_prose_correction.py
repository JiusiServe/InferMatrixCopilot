"""A correction cannot renew a wrong page by updating metadata alone."""
import pytest

from infermatrix_copilot.kb_service.maintenance_correction import correct_prose
from infermatrix_copilot.kb_service.maintenance_units import page_units
from infermatrix_copilot.knowledge_service.lifecycle import LifecycleError, Page


def test_identical_legacy_body_cannot_renew_content_or_updated_date():
    page = "repos/demo/core/architecture.md"
    text = ("---\ntitle: Queue\ncreated: 2026-09-01\nupdated: 2026-09-01\n"
            "type: architecture\ntags: [demo]\nsources: []\n---\n\n"
            "# Queue\n\nThe default capacity is sixteen.\n")
    unit = next(row for row in page_units(page, text, "demo", "original")
                if row["kind"] == "legacy")
    body = text[len(Page.parse(text).frontmatter):]
    files = {page: text}
    with pytest.raises(LifecycleError, match="must change"):
        correct_prose(files, unit, body, today="2026-10-08")
    assert files[page] == text
    _, corrected = correct_prose(files, unit, body.replace("sixteen", "eight"), today="2026-10-08")
    result = Page.parse(corrected.files[page])
    assert str(result.frontmatter_data()["updated"]) == "2026-10-08"
    assert "capacity is eight" in corrected.files[page]
