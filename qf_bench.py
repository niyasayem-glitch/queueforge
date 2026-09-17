"""queueforge tier-bench — single-file portable runner.

Works on ANY tier with python3. Proves the invented tool runs everywhere:
    python3 qf_bench.py [--tier local|cloud|gpu] [--n 3]
"""
from __future__ import annotations

import argparse
import json
import platform
import time

from core import MemoryQueue
from core.worker import run_worker


def bench(tier: str, n: int) -> dict:
    q = MemoryQueue()
    for i in range(n):
        q.submit(f"bench-{i}", {"sleep": 0.05})
    t0 = time.time()
    result = run_worker(q, platform.node(), max_tasks=n)
    elapsed = time.time() - t0
    return {
        "tool": "queueforge",
        "version": "0.1.0",
        "tier": tier,
        "hostname": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "n": n,
        "stats": q.stats(),
        "worker": result,
        "wall_s": round(elapsed, 3),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="local")
    ap.add_argument("--n", type=int, default=3)
    args = ap.parse_args()
    print(json.dumps(bench(args.tier, args.n), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())