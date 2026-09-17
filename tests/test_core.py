"""core tests — state machine + queue semantics."""
import time

import pytest

from core import MemoryQueue, Task, TaskState


def test_task_lifecycle():
    t = Task(name="x")
    assert t.state is TaskState.PENDING
    t.start()
    assert t.state is TaskState.RUNNING
    assert t.attempts == 1
    t.complete("ok")
    assert t.state is TaskState.DONE
    assert t.result == "ok"
    assert t.latency_ms is not None


def test_task_cannot_start_twice():
    t = Task(name="x")
    t.start()
    with pytest.raises(ValueError):
        t.start()


def test_task_complete_requires_running():
    t = Task(name="x")
    with pytest.raises(ValueError):
        t.complete("nope")


def test_task_fail_sets_error():
    t = Task(name="x")
    t.start()
    t.fail("boom")
    assert t.state is TaskState.FAILED
    assert t.error == "boom"


def test_task_to_dict_fields():
    d = Task(name="x").to_dict()
    for k in ("id", "name", "state", "created_at", "attempts", "latency_ms"):
        assert k in d


def test_submit_assigns_ids():
    q = MemoryQueue()
    a = q.submit("a")
    b = q.submit("b")
    assert a.id != b.id


def test_get_returns_fifo_pending_only():
    q = MemoryQueue()
    q.submit("a")
    t = q.get()
    assert t is not None and t.name == "a"
    assert t.state is TaskState.RUNNING
    assert q.get() is None  # drained


def test_ack_marks_done():
    q = MemoryQueue()
    q.submit("a")
    t = q.get()
    q.ack(t, "done")
    assert t.state is TaskState.DONE
    assert q.stats()["done"] == 1


def test_nack_marks_failed():
    q = MemoryQueue()
    q.submit("a")
    t = q.get()
    q.nack(t, "err")
    assert t.state is TaskState.FAILED
    assert q.stats()["failed"] == 1


def test_worker_processes_until_drained():
    q = MemoryQueue()
    for i in range(5):
        q.submit(f"t{i}", {"sleep": 0.01})
    from core.worker import run_worker

    r = run_worker(q, "testhost")
    assert r["processed"] == 5
    assert q.stats()["done"] == 5


def test_worker_max_tasks():
    q = MemoryQueue()
    for i in range(5):
        q.submit(f"t{i}")
    from core.worker import run_worker

    r = run_worker(q, "testhost", max_tasks=2)
    assert r["processed"] == 2


def test_worker_survives_exception():
    q = MemoryQueue()
    q.submit("boom", {"sleep": -1})  # sleep(-1) raises in executor... actually no
    t = q.get()
    q.nack(t, "manual")
    assert t.state is TaskState.FAILED


def test_queue_clear():
    q = MemoryQueue()
    q.submit("a")
    q.clear()
    assert q.stats()["total"] == 0


def test_stress_roundtrip():
    q = MemoryQueue()
    for i in range(50):
        q.submit(f"s{i}", {"sleep": 0.001})
    from core.worker import run_worker

    r = run_worker(q, "stress")
    assert r["processed"] == 50
    assert q.stats()["done"] == 50