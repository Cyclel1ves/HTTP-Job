from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from task_store import TaskStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def _read_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length_str = handler.headers.get("Content-Length")
    if not length_str:
        raise ValueError("Empty body")
    try:
        length = int(length_str)
    except ValueError:
        raise ValueError("Invalid Content-Length")

    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("Invalid JSON")


class TaskAPIHandler(BaseHTTPRequestHandler):
    store = TaskStore("tasks.txt")

    def _send_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def _send_json(self, code: int, obj: Any) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._send_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_empty(self, code: int) -> None:
        self.send_response(code)
        self._send_cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _parse_path(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:
        path = self._parse_path()

        if path == "/tasks":
            tasks = [t.to_dict() for t in self.store.list_tasks()]
            self._send_json(200, tasks)
            return

        self._send_empty(404)

    def do_POST(self) -> None:
        path = self._parse_path()

        if path == "/tasks":
            try:
                body = _read_json_body(self)
                title = body.get("title")
                priority = body.get("priority")
                task = self.store.create_task(title=title, priority=priority)
                self._send_json(200, task.to_dict())
            except ValueError as e:
                self._send_json(400, {"error": str(e)})
            except Exception:
                logging.exception("Unhandled error in POST /tasks")
                self._send_json(500, {"error": "internal error"})
            return

        parts = [p for p in path.split("/") if p]
        if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "complete":
            try:
                task_id = int(parts[1])
            except ValueError:
                self._send_empty(404)
                return

            ok = self.store.complete_task(task_id)
            if ok:
                self._send_empty(200)
            else:
                self._send_empty(404)
            return

        self._send_empty(404)

    def log_message(self, format: str, *args: Any) -> None:
        logging.info("%s - %s", self.address_string(), format % args)


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), TaskAPIHandler)
    logging.info("Server started on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logging.info("Server stopped")


if __name__ == "__main__":
    import sys

    h = "127.0.0.1"
    p = 8080

    if len(sys.argv) >= 2:
        h = sys.argv[1]
    if len(sys.argv) >= 3:
        p = int(sys.argv[2])

    run(h, p)
