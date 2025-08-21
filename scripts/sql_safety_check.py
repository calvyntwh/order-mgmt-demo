#!/usr/bin/env python3
"""Lightweight SQL safety scanner.

This script scans the repository for obvious SQL string concatenation patterns
that may indicate unparameterized queries. It is not a replacement for manual
code review or static analyzers, but provides a quick grep-based safety check
for the demo.

Usage:
  ./scripts/sql_safety_check.py

Exit codes:
  0 - no findings
  1 - potential risky patterns found
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

PATTERNS = [
    re.compile(r"\+\s*\w+\s*\+"),  # string + variable + string
    re.compile(r"%\(.*\)s"),  # printf-style formatting in a single string
    re.compile(r"format\(.*\)"),  # .format usage inside SQL context
]


def scan(root: Path) -> int:
    findings = []
    for p in root.rglob("*.py"):
        # Skip scanning the sql_safety_check.py script itself to avoid false positives
        if p.name == "sql_safety_check.py":
            continue
        try:
            text = p.read_text()
        except Exception:
            continue
        # naive heuristic: look for SQL-like keywords near pattern
        if "SELECT" in text or "INSERT" in text or "UPDATE" in text or "DELETE" in text:
            for lineno, line in enumerate(text.splitlines(), start=1):
                for pat in PATTERNS:
                    if pat.search(line):
                        findings.append((str(p), lineno, line.strip()))
    if findings:
        print("Potential un-parameterized SQL patterns found:")
        for f in findings:
            print(f" - {f[0]}:{f[1]}: {f[2]}")
        return 1
    print("No obvious SQL string concatenation patterns found")
    return 0


if __name__ == "__main__":
    rc = scan(Path("."))
    raise SystemExit(rc)
