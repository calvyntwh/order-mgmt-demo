import tempfile
from pathlib import Path

from scripts.mark_todo_done import mark_todo_done_file


def make_todo(contents: str) -> Path:
    fd, p = tempfile.mkstemp(prefix='todo_', suffix='.md')
    Path(p).write_text(contents, encoding='utf8')
    return Path(p)


def test_mark_by_id_exact():
    contents = """- [ ] [1] First task
- [ ] [2] Second task
"""
    p = make_todo(contents)
    changed = mark_todo_done_file(p, '2')
    assert len(changed) == 1
    text = p.read_text(encoding='utf8')
    assert '- [x] [2] Second task' in text


def test_mark_by_substring():
    contents = """- [ ] Fix gateway issue
- [ ] Another task
"""
    p = make_todo(contents)
    changed = mark_todo_done_file(p, 'gateway')
    assert len(changed) == 1
    assert '- [x] Fix gateway issue' in p.read_text(encoding='utf8')


def test_mark_all_flag():
    contents = """- [ ] common task A
- [ ] common task B
"""
    p = make_todo(contents)
    changed = mark_todo_done_file(p, 'common', mark_all=True)
    assert len(changed) == 2
    text = p.read_text(encoding='utf8')
    assert text.count('- [x]') == 2
