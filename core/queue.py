"""MemoryQueue — thread-safe in-process queue. Zero deps."""
from __future__ import annotations

import threading
import time
from collections import Counter

from .task import Task, TaskState


class MemoryQueue:
    """Thread-safe FIFO queue with state accounting."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._pending: list[str] = []  # FIFO of task ids
        self._lock = threading.RLock()

    def submit(self, name: str, payload: dict | None = None) -> Task:
        with self._lock:
            task = Task(name=name, payload=payload or {})
            self._tasks[task.id] = task
            self._pending.append(task.id)
            return task

    def get(self) -> Task | None:
        """Pop the oldest pending task (thread-safe)."""
        with self._lock:
            while self._pending:
                tid = self._pending.pop(0)
                task = self._tasks[tid]
                if task.state is TaskState.PENDING:
                    task.start()
                    return task
            return None

    def ack(self, task: Task, result: str) -> None:
        with self._lock:
            task.complete(result)

    def nack(self, task: Task, error: str) -> None:
        with self._lock:
            task.fail(error)

    def stats(self) -> dict:
        with self._lock:
            counts = Counter(t.state.value for t in self._tasks.values())
            return {
                "total": len(self._tasks),
                "pending": counts.get("pending", 0),
                "running": counts.get("running", 0),
                "done": counts.get("done", 0),
                "failed": counts.get("failed", 0),
            }

    def all_tasks(self) -> list[dict]:
        with self._lock:
            return [t.to_dict() for t in self._tasks.values()]

    def clear(self) -> None:
        with self._lock:
            self._tasks.clear()
            self._pending.clear()