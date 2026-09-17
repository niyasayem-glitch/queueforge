# queueforge

Distributed task queue platform — 5 packages + compose. Flat layout, zero-dep core.

| package | role |
|---|---|
| `core` | Task state machine + thread-safe MemoryQueue + worker loop (ZERO deps) |
| `api` | FastAPI REST layer (`uvicorn api.app:app`) |
| `monitor` | stdlib dashboard + `import_check()` — **the historical import fix** |
| `cli` | `python -m cli.cli submit|status|worker` |
| `worker` | standalone worker entrypoint |

## Quickstart

```bash
uv sync              # or: python3 -m venv .venv && .venv/bin/pip install pytest
python -m pytest -q              # 16 core tests, zero deps
python -m cli.cli status         # host signature + stats
python -m cli.cli submit hello --sleep 0.05
python -m cli.cli worker
python qf_bench.py --tier local --n 3   # portable tier-bench
python -c "import monitor; print(monitor.import_check())"  # THE FIX: imports clean
```

## Tier traversal

```bash
python qf_bench.py --tier local   # phone/proot
python qf_bench.py --tier cloud   # GitHub runner
python qf_bench.py --tier gpu     # Kaggle T4
```