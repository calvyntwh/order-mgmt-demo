#!/usr/bin/env python3
"""Simple HTTP benchmark for the demo services.

This lightweight script exercises a single endpoint repeatedly and reports
latency percentiles (p50/p90/p95/p99). It uses only the stdlib so it can run
in CI without extra packages.

Usage:
  ./scripts/benchmark.py --url http://localhost:8001/health --n 100

Exit code: 0 on success
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from statistics import median
from typing import List


def run_once(url: str, timeout: float = 5.0) -> float:
    start = time.monotonic()
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        # read at most small body to exercise the request
        resp.read(1024)
    return (time.monotonic() - start) * 1000.0


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Lightweight HTTP benchmark")
    parser.add_argument("--url", required=True, help="Full URL to hit")
    parser.add_argument("--n", type=int, default=100, help="Number of requests")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-request timeout (s)")
    args = parser.parse_args(argv)

    latencies: List[float] = []
    errors = 0
    for i in range(args.n):
        try:
            ms = run_once(args.url, timeout=args.timeout)
            latencies.append(ms)
        except Exception as exc:
            errors += 1
            print(f"Request {i+1}/{args.n} failed: {exc}")

    if not latencies:
        print("No successful requests")
        return 2

    print(f"Requests: {args.n}, Success: {len(latencies)}, Errors: {errors}")
    print(f"min: {min(latencies):.2f}ms")
    print(f"p50: {percentile(latencies, 50):.2f}ms")
    print(f"p90: {percentile(latencies, 90):.2f}ms")
    print(f"p95: {percentile(latencies, 95):.2f}ms")
    print(f"p99: {percentile(latencies, 99):.2f}ms")
    print(f"max: {max(latencies):.2f}ms")

    # Simple policy check: p95 target for /health should be < 200ms by default
    p95 = percentile(latencies, 95)
    if "/health" in args.url and p95 > 200:
        print(f"WARNING: p95 {p95:.2f}ms exceeds target 200ms")
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
