"""Source metadata must not become visible Markdown table rows."""
import shutil
import subprocess
from pathlib import Path

import pytest


WEB = Path(__file__).resolve().parents[1] / "src/infermatrix_copilot/rfc_service/web"


@pytest.mark.skipif(not shutil.which("node"), reason="Node is required for browser Markdown contracts")
def test_source_comments_are_hidden_without_enabling_html():
    program = f"""
import assert from 'node:assert/strict';
import {{createRequire}} from 'node:module';
import {{displayMarkdown}} from {(WEB / 'roadmap-markdown-display.mjs').as_uri()!r};
const require = createRequire(import.meta.url);
const md = require({str(WEB / 'markdown-it.min.js')!r})({{html:false}});
const body = '| PR | Status |\\n| --- | --- |\\n| #6844 | Merged |\\n<!-- roadmap-people: {{"6844":{{"author":"private-metadata"}}}} -->\\n<!-- roadmap-status:end -->\\n## Next';
const html = md.render(displayMarkdown(body));
assert.equal((html.match(/<tr>/g)||[]).length,2);
assert(!html.includes('roadmap-people')); assert(!html.includes('roadmap-status'));
assert(html.includes('<h2>Next</h2>')); assert(body.includes('private-metadata'));
assert.equal(displayMarkdown('Before\\n<!-- multiline\\nmetadata -->\\nAfter'),'Before\\n\\nAfter');
assert.equal(displayMarkdown('\\\\<!-- roadmap-status:end -->'),'');
for (const marker of ['```','~~~~']) {{
 const code = marker+'text\\n<!-- visible example -->\\n'+marker;
 assert.equal(displayMarkdown(code),code); assert(md.render(displayMarkdown(code)).includes('visible example'));
}}
const indented = '    <!-- code example -->'; assert.equal(displayMarkdown(indented),indented);
const inline = 'Text <!-- inline example --> remains'; assert.equal(displayMarkdown(inline),inline);
const malformed = '<!-- unfinished'; assert.equal(displayMarkdown(malformed),malformed);
assert(md.render(displayMarkdown('<script>alert(1)</script>')).includes('&lt;script&gt;'));
"""
    result = subprocess.run([shutil.which("node"), "--input-type=module"], input=program, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
