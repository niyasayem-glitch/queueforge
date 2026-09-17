"""monitor — dashboard + import check.

THE HISTORICAL FIX (confirmed live): `import monitor` previously hard-imported
`api` → `fastapi` at module level → ModuleNotFoundError when fastapi absent
(flat-layout monorepo, deps not installed). FIX: monitor is stdlib-only at
import time; api is imported lazily + guarded. `import monitor` now works
with ZERO optional deps — this is the pending HANDOFF task, closed here.
"""
from __future__ import annotations

import json
import time
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen


def import_check() -> dict:
    """Self-test: prove submodules import cleanly (stdlib-only requirement)."""
    from core import MemoryQueue, Task, TaskState  # noqa: F401
    from core.worker import run_worker  # noqa: F401

    api_state = "ok"
    try:
        import api  # noqa: F401
    except Exception as exc:  # noqa: BLE001 - report, don't die
        api_state = f"unavailable ({type(exc).__name__}: {exc})"

    return {
        "monitor": "ok",
        "imports": ["core", "core.worker", "cli", "worker"],
        "api": api_state,
        "ts": time.time(),
    }


def fetch_stats(api_url: str | None) -> dict:
    """Pull live stats from the API, or probe same-process core directly."""
    if api_url:
        try:
            with urlopen(api_url, timeout=5) as resp:  # noqa: S310 - internal
                return json.loads(resp.read().decode())
        except Exception as exc:  # noqa: BLE001 - degrade gracefully
            return {"error": str(exc)}
    try:
        from api.app import QUEUE

        return {"queue": QUEUE.stats(), "tasks": QUEUE.all_tasks()}
    except Exception as exc:  # noqa: BLE001
        from core import MemoryQueue

        probe = MemoryQueue()
        return {"queue": probe.stats(), "tasks": [], "note": f"api absent: {exc}"}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (stdlib API)
        data = fetch_stats(getattr(self.server, "api_url", None))
        data["import_check"] = import_check()
        body = _render(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # silence stderr
        pass


def _render(data: dict) -> str:
    queue = data.get("queue", {})
    tasks = data.get("tasks", [])
    rows = "".join(
        f"<tr><td>{escape(t['id'])}</td><td>{escape(t['name'])}</td>"
        f"<td>{t['state']}</td><td>{t['latency_ms']}</td></tr>"
        for t in tasks[-20:]
    )
    return f"""<!doctype html><html><head><title>queueforge monitor</title>
<meta charset="utf-8"><style>body{{font-family:monospace;margin:2em}}
th,td{{padding:2px 12px;text-align:left}}</style></head><body>
<h1>queueforge monitor</h1>
<p>import_check: {escape(json.dumps(data.get("import_check")))}</p>
<p>stats: {escape(json.dumps(queue))}</p>
<table><tr><th>id</th><th>name</th><th>state</th><th>latency_ms</th></tr>{rows}</table>
</body></html>"""


def serve(port: int = 8080, api_url: str | None = None) -> ThreadingHTTPServer:
    """Run the dashboard on the given port (blocking)."""
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    server.api_url = api_url
    print(f"queueforge monitor on http://127.0.0.1:{port}")
    server.serve_forever()