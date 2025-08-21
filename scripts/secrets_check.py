#!/usr/bin/env python3
"""Secrets and password scanner for the order-mgmt-demo repository.

This script scans for hardcoded secrets, passwords, API keys, and other sensitive
information that should not be committed to the repository. It complements the
existing validate_env.py and sql_safety_check.py scripts.

Usage:
  ./scripts/secrets_check.py
  ./scripts/secrets_check.py --include-tests  # include test files in scan

Exit codes:
  0 - no findings
  1 - potential secrets found
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    file_path: str
    line_number: int
    line_content: str
    pattern_name: str
    severity: str  # "HIGH", "MEDIUM", "LOW"


# Patterns to detect various types of secrets and passwords
SECRET_PATTERNS = {
    # High severity - definite secrets that should never be hardcoded
    "hardcoded_jwt_secret": {
        "pattern": re.compile(r'["\']dev-secret["\']', re.IGNORECASE),
        "severity": "HIGH",
        "description": "Hardcoded JWT secret 'dev-secret' should use environment variables"
    },
    "generic_password_assignment": {
        "pattern": re.compile(r'password\s*=\s*["\'][^"\']{3,}["\']', re.IGNORECASE),
        "severity": "HIGH",
        "description": "Hardcoded password assignment"
    },
    "api_key_assignment": {
        "pattern": re.compile(r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', re.IGNORECASE),
        "severity": "HIGH",
        "description": "Hardcoded API key assignment"
    },
    "secret_assignment": {
        "pattern": re.compile(r'secret\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
        "severity": "HIGH",
        "description": "Hardcoded secret assignment"
    },
    
    # Medium severity - potentially problematic
    "database_url_with_password": {
        "pattern": re.compile(r'postgresql://[^:]+:[^@]+@[^/]+', re.IGNORECASE),
        "severity": "MEDIUM",
        "description": "Database URL with embedded credentials"
    },
    "postgres_url_with_password": {
        "pattern": re.compile(r'postgres://[^:]+:[^@]+@[^/]+', re.IGNORECASE),
        "severity": "MEDIUM",
        "description": "Postgres URL with embedded credentials"
    },
    "mysql_url_with_password": {
        "pattern": re.compile(r'mysql://[^:]+:[^@]+@[^/]+', re.IGNORECASE),
        "severity": "MEDIUM",
        "description": "MySQL URL with embedded credentials"
    },
    "weak_test_passwords": {
        "pattern": re.compile(r'["\'](?:admin(?:pass)?123|test123|password123|secret123)["\']', re.IGNORECASE),
        "severity": "MEDIUM",
        "description": "Weak test password that could be used maliciously"
    },
    "bcrypt_hash": {
        "pattern": re.compile(r'["\'][\$]2[aby][\$]\d+[\$][./A-Za-z0-9]{53,}["\']'),
        "severity": "MEDIUM",
        "description": "Hardcoded bcrypt hash (review if this is for seeding/testing)"
    },
    
    # Low severity - worth reviewing but may be acceptable
    "base64_like_strings": {
        "pattern": re.compile(r'["\'][A-Za-z0-9+/]{32,}={0,2}["\']'),
        "severity": "LOW",
        "description": "Base64-like string that could be an encoded secret"
    },
    "jwt_token_like": {
        "pattern": re.compile(r'["\']eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*["\']'),
        "severity": "LOW",
        "description": "JWT-like token structure"
    },
}

# Files and patterns to exclude from scanning
EXCLUSIONS = {
    # Files that are expected to contain test data or examples
    "paths": {
        ".git/",
        "__pycache__/",
        ".pytest_cache/",
        ".venv/",
        "venv/",
        "node_modules/",
        ".ruff_cache/",
    },
    # Specific files to exclude (like this scanner itself)
    "files": {
        "scripts/secrets_check.py",  # Don't scan the scanner itself
    },
    # Lines containing these patterns are likely false positives
    "line_patterns": {
        re.compile(r'#.*noqa.*S105'),  # bandit ignore for hardcoded password
        re.compile(r'#.*test literal'),  # test literal marker
        re.compile(r'#.*example'),  # example marker
        re.compile(r'#.*placeholder'),  # placeholder marker
        re.compile(r'#.*demo.*credentials'),  # demo credentials
        re.compile(r'#.*pattern.*regex'),  # regex pattern definitions
    },
}


def should_exclude_file(file_path: Path, include_tests: bool) -> bool:
    """Check if a file should be excluded from scanning."""
    path_str = str(file_path)
    
    # Exclude based on path patterns
    for excluded_path in EXCLUSIONS["paths"]:
        if excluded_path in path_str:
            return True
    
    # Exclude specific files
    for excluded_file in EXCLUSIONS["files"]:
        if path_str.endswith(excluded_file) or excluded_file in path_str:
            return True
    
    # Exclude test files unless explicitly included
    if not include_tests and ("/test" in path_str or "test_" in file_path.name):
        return True
    
    return False


def should_exclude_line(line: str) -> bool:
    """Check if a line should be excluded from scanning based on comments or markers."""
    for pattern in EXCLUSIONS["line_patterns"]:
        if pattern.search(line):
            return True
    return False


def scan_file(file_path: Path, include_tests: bool) -> list[Finding]:
    """Scan a single file for secrets and return findings."""
    if should_exclude_file(file_path, include_tests):
        return []
    
    findings = []
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []
    
    for line_no, line in enumerate(content.splitlines(), start=1):
        if should_exclude_line(line):
            continue
        
        for pattern_name, pattern_info in SECRET_PATTERNS.items():
            if pattern_info["pattern"].search(line):
                findings.append(Finding(
                    file_path=str(file_path),
                    line_number=line_no,
                    line_content=line.strip(),
                    pattern_name=pattern_name,
                    severity=pattern_info["severity"]
                ))
    
    return findings


def scan_repository(root_path: Path, include_tests: bool) -> list[Finding]:
    """Scan the entire repository for secrets."""
    all_findings = []
    
    # File extensions to scan
    extensions = {".py", ".yml", ".yaml", ".json", ".toml", ".env", ".sh", ".sql"}
    
    for file_path in root_path.rglob("*"):
        if file_path.is_file() and (file_path.suffix in extensions or file_path.name.startswith(".env")):
            findings = scan_file(file_path, include_tests)
            all_findings.extend(findings)
    
    return all_findings


def group_findings_by_severity(findings: list[Finding]) -> dict[str, list[Finding]]:
    """Group findings by severity level."""
    grouped = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for finding in findings:
        grouped[finding.severity].append(finding)
    return grouped


def print_findings(findings: list[Finding]) -> None:
    """Print findings in a readable format."""
    if not findings:
        print("✅ No secrets or hardcoded passwords found!")
        return
    
    grouped = group_findings_by_severity(findings)
    
    total_high = len(grouped["HIGH"])
    total_medium = len(grouped["MEDIUM"])
    total_low = len(grouped["LOW"])
    
    print(f"🔍 Found {len(findings)} potential secrets/passwords:")
    print(f"   • {total_high} HIGH severity (should be fixed)")
    print(f"   • {total_medium} MEDIUM severity (review recommended)")
    print(f"   • {total_low} LOW severity (informational)")
    print()
    
    for severity in ["HIGH", "MEDIUM", "LOW"]:
        if not grouped[severity]:
            continue
        
        emoji = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "ℹ️"}[severity]
        print(f"{emoji} {severity} SEVERITY FINDINGS:")
        
        for finding in grouped[severity]:
            pattern_info = SECRET_PATTERNS[finding.pattern_name]
            print(f"  📁 {finding.file_path}:{finding.line_number}")
            print(f"     {pattern_info['description']}")
            print(f"     📋 {finding.line_content}")
            print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scan for secrets and passwords in the repository")
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in the scan (they are excluded by default)"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Root directory to scan (default: current directory)"
    )
    
    args = parser.parse_args()
    
    if not args.root.exists():
        print(f"❌ Error: Directory {args.root} does not exist")
        return 1
    
    print(f"🔍 Scanning {args.root} for secrets and passwords...")
    if not args.include_tests:
        print("   (excluding test files - use --include-tests to include them)")
    print()
    
    findings = scan_repository(args.root, args.include_tests)
    print_findings(findings)
    
    # Return exit code based on high severity findings
    high_severity_count = sum(1 for f in findings if f.severity == "HIGH")
    if high_severity_count > 0:
        print(f"❌ Found {high_severity_count} high-severity issues that should be addressed.")
        print("\n💡 Recommendations:")
        print("   • Replace hardcoded secrets with environment variables")
        print("   • Use GitHub Secrets for CI/CD pipelines")
        print("   • Consider using a secrets management service for production")
        print("   • Review database connection strings for embedded credentials")
        return 1
    
    medium_severity_count = sum(1 for f in findings if f.severity == "MEDIUM")
    if medium_severity_count > 0:
        print(f"⚠️  Found {medium_severity_count} medium-severity issues worth reviewing.")
        print("   Consider whether these are acceptable for your security requirements.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())