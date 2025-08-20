#!/usr/bin/env python3
"""Lightweight environment validator for the demo repo.

Usage:
  # local (non-fatal): prints warnings and suggests .env.dev
  ./scripts/validate_env.py

  # CI (fatal on missing/weak values)
  ./scripts/validate_env.py --ci

This script purposely avoids heavy dependencies. It uses stdlib only and
emits exit code 1 when run with --ci and checks fail. It validates:
  - JWT_SECRET presence & length
  - DATABASE_URL presence
  - BCRYPT_ROUNDS presence and minimum value
  - optional: checks that DB URL is not a localhost placeholder when --ci

It can also print a suggested `.env.dev` with random secrets for local development.
"""
from __future__ import annotations

import argparse
import base64
import os
import secrets
import sys
from typing import Dict, List


MIN_JWT_SECRET_LEN = 32
# Align bcrypt threshold with auth-service settings (recommend >= 12)
MIN_BCRYPT_ROUNDS = 12


def gen_random_secret(nbytes: int = 32) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).decode().rstrip("=")


def check_env(ci: bool = False) -> int:
    issues: List[str] = []
    warnings: List[str] = []

    jwt = os.getenv("JWT_SECRET")
    if not jwt:
        msg = "JWT_SECRET is not set"
        if ci:
            issues.append(msg)
        else:
            warnings.append(msg)
    elif len(jwt) < MIN_JWT_SECRET_LEN:
        msg = f"JWT_SECRET is too short (len={len(jwt)}), recommend >= {MIN_JWT_SECRET_LEN}"
        if ci:
            issues.append(msg)
        else:
            warnings.append(msg)

    db = os.getenv("DATABASE_URL")
    if not db:
        msg = "DATABASE_URL is not set"
        if ci:
            issues.append(msg)
        else:
            warnings.append(msg)
    else:
        if ci and db.startswith("sqlite://"):
            issues.append("DATABASE_URL uses sqlite in CI; use a real Postgres URL for integration tests")

    bcrypt_rounds = os.getenv("BCRYPT_ROUNDS")
    if bcrypt_rounds is None:
        msg = f"BCRYPT_ROUNDS not set (recommend >= {MIN_BCRYPT_ROUNDS})"
        if ci:
            issues.append(msg)
        else:
            warnings.append(msg)
    else:
        try:
            r = int(bcrypt_rounds)
            if r < MIN_BCRYPT_ROUNDS:
                msg = f"BCRYPT_ROUNDS is {r}; consider >= {MIN_BCRYPT_ROUNDS}"
                if ci:
                    issues.append(msg)
                else:
                    warnings.append(msg)
        except ValueError:
            issues.append("BCRYPT_ROUNDS must be an integer")

    # Optional additional checks
    valkey = os.getenv("VALKEY_URL")
    if valkey is None:
        warnings.append("VALKEY_URL not set; sessions will use in-memory fallback")

    if issues:
        print("ERROR: Environment validation failed with the following issues:")
        for i in issues:
            print("  -", i)
        print()
        print("Run this script without --ci to see non-fatal warnings and a suggested .env.dev")
        return 1

    if warnings:
        print("Warnings:")
        for w in warnings:
            print("  -", w)
        print()

    return 0


def suggest_env() -> Dict[str, str]:
    return {
        "JWT_SECRET": gen_random_secret(48),
        "DATABASE_URL": "postgres://postgres:postgres@localhost:5432/demo",
        "BCRYPT_ROUNDS": str(max(MIN_BCRYPT_ROUNDS, 12)),
        "VALKEY_URL": "",  # leave blank for local dev
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate environment variables for order-mgmt-demo")
    parser.add_argument("--ci", action="store_true", help="Fail on missing or weak values (CI mode)")
    parser.add_argument("--suggest", action="store_true", help="Print a suggested .env.dev with safe defaults")
    args = parser.parse_args(argv)

    rc = check_env(ci=args.ci)
    if rc != 0:
        return rc

    if args.suggest:
        env = suggest_env()
        print("# Suggested .env.dev (do NOT use in production)")
        for k, v in env.items():
            print(f"{k}={v}")

    print("Environment validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
