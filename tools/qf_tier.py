#!/usr/bin/env python3
"""qf_tier — queueforge tier probe (FUTURE invented tool, 2026-09-17).

Single-file, stdlib-only, runs on ANY tier (phone proot / GH runner / GPU kernel).
Proves tier-traversal: same tool, same code, distinct fingerprints + bench.

Usage:
    python3 qf_tier.py --tier local [--n 20000]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
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


def parity(n: int) -> dict[str, object]:
    """Deterministic cross-tier checksum — SAME value on every arch/tier.

    This is what turns 'ran on 3 tiers' into 'ran the SAME computation on 3
    tiers': compare sha256_16 across tiers; a mismatch = real divergence.
    """
    s = bytearray([1]) * (n + 1)
    s[0] = s[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if s[i]:
            s[i * i :: i] = b"\x00" * (((n - i * i) // i) + 1)
    count = sum(s)
    digest = hashlib.sha256(f"primes<={n}={count}".encode()).hexdigest()[:16]
    return {"n": n, "primes": count, "sha256_16": digest}


def gpu_probe() -> dict:
    """Probe for a visible GPU on this tier via nvidia-smi. Never raises.

    v0.3: tier self-description — every run of the tool reports whether a GPU
    is reachable where it executes. On GPU kernels (kaggle/colab) this yields
    the real hardware line; on CPU tiers it degrades gracefully. The kaggle
    JSON can then be diffed against this field without code changes.
    """
    smi = shutil.which("nvidia-smi")
    if not smi:
        return {"present": False, "reason": "no nvidia-smi binary"}
    try:
        r = subprocess.run(
            [smi, "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as exc:  # noqa: BLE001 - report, don't die
        return {"present": False, "reason": f"nvidia-smi failed: {type(exc).__name__}"}
    if r.returncode != 0:
        return {"present": False,
                "reason": f"nvidia-smi rc={r.returncode}: {r.stderr.strip()[:80]}"}
    return {"present": True, "line": r.stdout.strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description="queueforge tier probe")
    ap.add_argument("--tier", default="local", help="local|cloud|gpu")
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--parity-n", type=int, default=200000,
                    help="deterministic cross-tier checksum size")
    ap.add_argument("--no-gpu-probe", action="store_true",
                    help="skip nvidia-smi probe (fast path)")
    args = ap.parse_args()

    out = {
        "tool": "qf_tier",
        "version": "0.3.0",
        "tier": args.tier,
        "hostname": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "ncpu": os.cpu_count(),
        "n": args.n,
        "ops_per_s": bench(args.n),
        "parity": parity(args.parity_n),
        "gpu": None if args.no_gpu_probe else gpu_probe(),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())