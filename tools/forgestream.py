#!/usr/bin/env python3
"""forgestream — cross-tier BYTE-STREAM determinism probe (FUTURE invented tool, 2026-09-17).

Single-file, stdlib-only. Runs on ANY tier (phone proot / GH runner / GPU kernel).

NEW CAPABILITY vs qf_tier (ops/s + primer parity) and tiermesh (sieve parity):
proves that a deterministic BYTE STREAM — not just a count — is bit-identical
across tiers. random.Random(seed).getrandbits(32) returns exactly one raw
MT19937 state word (CPython k<=32 fast path, Matsumoto-Nishimura algorithm,
arch-independent), and we encode it big-endian -> the sha256 of the whole
stream MUST be identical on aarch64 phone, x86_64 cloud runner, and any GPU
kernel that runs the same code. This is the property distributed sampling /
federated seeding / reproducible data pipelines need.

Usage (cli):    python3 forgestream.py --tier local [--n 1200000] [--seed 42]
Usage (env, quote-free CI exec per cyc16/18):  FS_TIER=cloud FS_N=1200000 FS_SEED=42 python3 forgestream.py
"""
import argparse
import hashlib
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import time


def stream(n: int, seed: int) -> bytes:
    """Generate n MT19937 words via getrandbits(32) -> 4B big-endian each.

    Deterministic across CPython versions AND platforms: getrandbits(k<=32)
    is the raw genrand_uint32() output; big-endian encoding is fixed, so no
    host endianness can leak into the bytes.
    """
    r = random.Random(seed)
    ba = bytearray()
    chunk = 1 << 20  # 1M words per join chunk -> bounded memory (~n*4 bytes)
    rem = n
    while rem > 0:
        c = chunk if rem > chunk else rem
        ba += b"".join(r.getrandbits(32).to_bytes(4, "big") for _ in range(c))
        rem -= c
    return bytes(ba)


def parity(n: int, seed: int) -> dict:
    t0 = time.perf_counter()
    data = stream(n, seed)
    gen_s = time.perf_counter() - t0
    h = hashlib.sha256(data).hexdigest()
    return {
        "n_words": n,
        "seed": seed,
        "n_bytes": len(data),
        "sha256_16": h[:16],
        "sha256_full": h,
        "words_per_s": round(n / gen_s, 1) if gen_s > 0 else 0.0,
    }


def gpu_probe() -> dict:
    smi = shutil.which("nvidia-smi")
    if not smi:
        return {"present": False, "reason": "no nvidia-smi binary"}
    try:
        out = subprocess.run(
            [smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        return {"present": True, "smi": out.stdout.strip().splitlines()[:1] or []}
    except Exception as e:  # pragma: no cover - defensive
        return {"present": False, "reason": f"smi error: {type(e).__name__}"}


def tier_id() -> dict:
    return {
        "machine": platform.machine(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ncpu": os.cpu_count(),
        "hostname": platform.node(),
    }


def run(tier: str, n: int, seed: int) -> dict:
    return {
        "tool": "forgestream v1.0.0",
        "tier": tier,
        "tier_id": tier_id(),
        "gpu": gpu_probe(),
        "parity": parity(n, seed),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="cross-tier byte-stream determinism probe")
    ap.add_argument("--tier", default="local")
    ap.add_argument("--n", type=int, default=1_200_000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    # env mode overrides (quote-free CI exec)
    tier = os.environ.get("FS_TIER", a.tier)
    n = int(os.environ.get("FS_N", a.n))
    seed = int(os.environ.get("FS_SEED", a.seed))

    out = run(tier, n, seed)
    # quote-free-safe stdout marker for piped CI: bare int marker + chr(124)
    print(77, json.dumps(out), sep=chr(124))
    return 0


if __name__ == "__main__":
    sys.exit(main())