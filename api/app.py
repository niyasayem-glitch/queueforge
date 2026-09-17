"""api — FastAPI REST layer over core.MemoryQueue."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from core import MemoryQueue, Task
from core.worker import run_worker

app = FastAPI(title="queueforge", version="0.1.0")
QUEUE = MemoryQueue()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "queue": QUEUE.stats()}


@app.post("/tasks")
def submit(name: str, payload: dict | None = None) -> dict:
    task = QUEUE.submit(name, payload)
    return task.to_dict()


@app.get("/tasks")
def list_tasks() -> list[dict]:
    return QUEUE.all_tasks()


@app.post("/tasks/drain")
def drain(max_tasks: int = 0) -> dict:
    """Run the worker against this API's in-process queue (API-hosted worker)."""
    return run_worker(QUEUE, "api-host", max_tasks)


@app.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    for t in QUEUE.all_tasks():
        if t["id"] == task_id:
            return t
    raise HTTPException(status_code=404, detail="task not found")


@app.post("/tasks/{task_id}/ack")
def ack(task_id: str, result: str = "done") -> dict:
    task = _find(task_id)
    QUEUE.ack(task, result)
    return task.to_dict()


@app.post("/tasks/{task_id}/nack")
def nack(task_id: str, error: str = "worker error") -> dict:
    task = _find(task_id)
    QUEUE.nack(task, error)
    return task.to_dict()


def _find(task_id: str):
    tasks = QUEUE.all_tasks()
    for t in tasks:
        if t["id"] == task_id:
            tid = task_id
            break
    else:
        raise HTTPException(status_code=404, detail="task not found")
    # MemoryQueue.get returns the in-memory Task object; rebuild lookup here.
    task = QUEUE._tasks[tid]  # noqa: SLF001 - same-process convenience
    return task