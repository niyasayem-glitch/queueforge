"""Task model with explicit state machine — zero deps."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    """A single unit of work."""

    name: str
    payload: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: TaskState = TaskState.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    result: str | None = None
    error: str | None = None
    attempts: int = 0

    def start(self) -> None:
        if self.state is not TaskState.PENDING:
            raise ValueError(f"cannot start task in {self.state.value}")
        self.state = TaskState.RUNNING
        self.started_at = time.time()
        self.attempts += 1

    def complete(self, result: str) -> None:
        if self.state is not TaskState.RUNNING:
            raise ValueError(f"cannot complete task in {self.state.value}")
        self.state = TaskState.DONE
        self.result = result
        self.finished_at = time.time()

    def fail(self, error: str) -> None:
        self.state = TaskState.FAILED
        self.error = error
        self.finished_at = time.time()

    @property
    def latency_ms(self) -> float | None:
        if self.finished_at is not None and self.created_at is not None:
            return round((self.finished_at - self.created_at) * 1000, 2)
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "state": self.state.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "result": self.result,
            "error": self.error,
            "attempts": self.attempts,
            "latency_ms": self.latency_ms,
        }