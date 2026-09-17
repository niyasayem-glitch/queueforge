"""worker — standalone worker entrypoint (dependency-free)."""
from __future__ import annotations

import platform
import sys

from core import MemoryQueue
from core.worker import run_worker


def main(argv: list[str] | None = None) -> int:
    q = MemoryQueue()
    sig = {
        "hostname": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "tier": "local",
    }
    result = run_worker(q, sig["hostname"])
    print(f"worker[{sig['machine']}] tier={sig['tier']} host={sig['hostname']} → {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())