"""cli — submit/status/worker commands (stdlib + core only)."""
from __future__ import annotations

import argparse
import json
import platform
import sys

from core import MemoryQueue
from core.worker import run_worker


def _host_sig() -> dict:
    return {
        "hostname": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


def cmd_submit(q: MemoryQueue, args) -> int:
    task = q.submit(args.name, {"sleep": args.sleep})
    print(json.dumps({"submitted": task.to_dict()}, indent=2))
    return 0


def cmd_status(q: MemoryQueue, args) -> int:
    print(json.dumps({"stats": q.stats(), "host": _host_sig()}, indent=2))
    return 0


def cmd_worker(q: MemoryQueue, args) -> int:
    print(json.dumps(run_worker(q, _host_sig()["hostname"], args.max_tasks), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="queueforge", description="task queue CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_submit = sub.add_parser("submit", help="enqueue a task")
    p_submit.add_argument("name")
    p_submit.add_argument("--sleep", type=float, default=0.0)

    p_status = sub.add_parser("status", help="queue stats + host signature")

    p_worker = sub.add_parser("worker", help="process pending tasks")
    p_worker.add_argument("--max-tasks", type=int, default=0)

    args = parser.parse_args(argv)
    q = MemoryQueue()
    router = {"submit": cmd_submit, "status": cmd_status, "worker": cmd_worker}
    return router[args.cmd](q, args)


if __name__ == "__main__":
    sys.exit(main())