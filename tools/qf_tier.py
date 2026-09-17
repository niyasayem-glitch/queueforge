#!/usr/bin/env python3
"""qf_tier — queueforge tier probe (FUTURE invented tool, 2026-09-17).

Single-file, stdlib-only, runs on ANY tier (phone proot / GH runner / GPU kernel).
Proves tier-traversal: same tool, same code, distinct fingerprints + bench.

Usage:
    python3 qf_tier.py --tier local [--n 20000]
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import time
from collections import deque


def bench(n: int) -> float:
    """Deterministic FIFO queue drain throughput (ops/sec)."""
    q: deque[int] = deque(range(n))
    t0 = time.perf_counter()
    while q:
        q.popleft()
    dt = time.perf_counter() - t0
    return round(n / dt, 1) if dt > 0 else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="queueforge tier probe")
    ap.add_argument("--tier", default="local", help="local|cloud|gpu")
    ap.add_argument("--n", type=int, default=20000)
    args = ap.parse_args()

    out = {
        "tool": "qf_tier",
        "version": "0.1.0",
        "tier": args.tier,
        "hostname": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "ncpu": os.cpu_count(),
        "n": args.n,
        "ops_per_s": bench(args.n),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())