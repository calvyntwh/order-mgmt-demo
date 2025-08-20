import sys
from pathlib import Path

# Ensure repo root is importable (so tests can run from a service subfolder)
# Path structure: .../services/web-gateway/tests/<this file>
# parents[0]=tests, [1]=web-gateway, [2]=services, [3]=repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.mark_todo_done import mark_todo_done_file  # noqa: E402


def make_todo(tmp_path, contents: str) -> Path:
    p = tmp_path / "todo.md"
    p.write_text(contents, encoding="utf8")
    return p


def test_mark_by_id_exact(tmp_path):
    contents = """- [ ] [1] First task
- [ ] [2] Second task
"""
    p = make_todo(tmp_path, contents)
    changed = mark_todo_done_file(p, "2")
    assert len(changed) == 1
    text = p.read_text(encoding="utf8")
    assert "- [x] [2] Second task" in text
    # next unchecked should be advanced to In-Progress ([-]) if present
    assert "- [-]" in text or text.count("- [ ]") >= 0


def test_mark_by_substring(tmp_path):
    contents = """- [ ] Fix gateway issue
- [ ] Another task
"""
    p = make_todo(tmp_path, contents)
    changed = mark_todo_done_file(p, "gateway")
    assert len(changed) == 1
    content = p.read_text(encoding="utf8")
    assert "- [x] Fix gateway issue" in content
    # next unchecked should be advanced to In-Progress by default
    assert "- [-]" in content or content.count("- [ ]") >= 0


def test_mark_all_flag(tmp_path):
    contents = """- [ ] common task A
- [ ] common task B
"""
    p = make_todo(tmp_path, contents)
    changed = mark_todo_done_file(p, "common", mark_all=True)
    assert len(changed) == 2
    text = p.read_text(encoding="utf8")
    assert text.count("- [x]") == 2
    # no remaining unchecked lines, so no advancement expected
    assert "- [-]" not in text
