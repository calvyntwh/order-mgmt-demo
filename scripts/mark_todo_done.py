#!/usr/bin/env python3
"""
mark_todo_done.py

Improved helper to mark todo items done in todo.md. Designed to be importable and testable.

Features:
- Match by exact numeric id (e.g. 6 or [6])
- Match by substring
- Optionally mark all matching unchecked items with --all

Examples:
    python scripts/mark_todo_done.py 6
    python scripts/mark_todo_done.py "Fix gateway" --all
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List


def mark_todo_done_file(path: Path, query: str, mark_all: bool = False, advance_next: bool = True) -> List[str]:
    """Mark matching unchecked todo lines as done.

    Returns list of lines that were changed.
    Raises FileNotFoundError if file not found.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    text = path.read_text(encoding='utf8')
    lines = text.splitlines()

    changed: List[str] = []
    changed_indices: List[int] = []

    # detect if query is simple numeric id like 6 or [6]
    m = re.fullmatch(r"\[?(\d+)\]?", query.strip())
    if m:
        tid = m.group(1)
        # match patterns like '- [ ] [6]' or '- [ ] [6] ' or '- [ ] [6] Description'
        id_pattern = re.compile(r"^-\s*\[\s*\]\s*\[" + re.escape(tid) + r"\]")
        for i, line in enumerate(lines):
            if id_pattern.search(line):
                if line.strip().startswith('- [ ]'):
                    lines[i] = line.replace('- [ ]', '- [x]', 1)
                    changed.append(line)
                    changed_indices.append(i)
                    if not mark_all:
                        break
    else:
        # substring match
        for i, line in enumerate(lines):
            if query in line and line.strip().startswith('- [ ]'):
                lines[i] = line.replace('- [ ]', '- [x]', 1)
                changed.append(line)
                changed_indices.append(i)
                if not mark_all:
                    break

    if not changed:
        return []

    # Optionally advance the next unchecked task to In-Progress ([-])
    if advance_next and changed_indices:
        last_changed = max(changed_indices)
        for j in range(last_changed + 1, len(lines)):
            if lines[j].strip().startswith('- [ ]'):
                # mark next unchecked task as In-Progress but do not include
                # this advancement in the `changed` list (changed is intended
                # to represent items marked done).
                lines[j] = lines[j].replace('- [ ]', '- [-]', 1)
                break

    path.write_text('\n'.join(lines) + '\n', encoding='utf8')
    return changed


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Mark a todo.md item as done')
    p.add_argument('query', help='task id (6 or [6]) or a substring to match')
    p.add_argument('--all', '-a', action='store_true', help='mark all matching unchecked items')
    p.add_argument('--no-advance', action='store_true', help='do not advance the next unchecked task to In-Progress')
    p.add_argument('--file', '-f', default='todo.md', help='path to todo.md')
    args = p.parse_args(argv)

    path = Path(args.file)
    advance_flag = not args.no_advance
    try:
        changed = mark_todo_done_file(path, args.query, mark_all=args.all, advance_next=advance_flag)
    except FileNotFoundError:
        print(f'ERROR: {path} not found')
        return 2

    if not changed:
        print(f'No matching unchecked todo line found for: {args.query}')
        return 1

    for original in changed:
        print(f'Marked: {original.strip()}')
    print('\nPlease review, commit, and push the change in the same branch.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
