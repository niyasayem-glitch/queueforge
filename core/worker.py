"""core worker — dependency-free process loop."""
from __future__ import annotations

import time

from .queue import MemoryQueue
from .task import Task


def run_worker(queue: MemoryQueue, hostname: str, max_tasks: int = 0) -> dict:
    """Process tasks until the queue drains or max_tasks is reached.

    Returns aggregate stats. Safe to call in any Python 3.10+ runtime.
    """
    processed = 0
    started = time.time()
    while True:
        if max_tasks and processed >= max_tasks:
            break
        task = queue.get()
        if task is None:
            break
        processed += 1
        try:
            result = _execute(task)
            queue.ack(task, result)
        except Exception as exc:  # noqa: BLE001 - worker must never die
            queue.nack(task, f"{type(exc).__name__}: {exc}")
    elapsed = round(time.time() - started, 3)
    return {"processed": processed, "elapsed_s": elapsed, "hostname": hostname}


def _execute(task: Task) -> str:
    """Default executor — echo with payload.

    The task payload may carry a 'sleep' key (seconds) to simulate work.
    """
    sleep = float(task.payload.get("sleep", 0.0) or 0.0)
    if sleep > 0:
        time.sleep(sleep)
    return "ok:" + task.name