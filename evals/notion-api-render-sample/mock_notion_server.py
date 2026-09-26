#!/usr/bin/env python3
"""mock_notion_server.py — mock HTTP para el eval battery del renderer Notion API (F55).

Servidor simple que responde a los endpoints de Notion con respuestas
predecibles. Soporta:
  - GET /v1/databases/{id}            → lista de properties preconfigurada
  - POST /v1/databases/{id}/query     → search con filtro
  - POST /v1/search                   → búsqueda global
  - POST /v1/pages                    → crear página (devuelve page_id predecible)
  - PATCH /v1/pages/{id}              → update properties
  - GET /v1/blocks/{id}/children      → lista de children
  - PATCH /v1/blocks/{id}/children    → append children
  - DELETE /v1/blocks/{id}            → delete block

Las respuestas se controlan por `MockState` que el test puede mutar
(retries, idempotencia, etc.).

Stdlib puro: http.server.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional


class MockState:
    """Estado compartido entre requests."""
    def __init__(self) -> None:
        self.pages: Dict[str, dict] = {}  # page_id → page dict
        self.page_by_note: Dict[str, str] = {}  # note_id → page_id
        self.database_properties: List[str] = [
            "name", "title", "notemartin_note_id", "notemartin_source_hash",
            "notemartin_ir_sha256", "notemartin_rendered_at",
            "notemartin_renderer_version", "author", "priority",
            "is_published", "url_field",
        ]
        self.call_log: List[dict] = []   # [{method, path, body}]
        self.response_overrides: Dict[str, Any] = {}  # path-prefix → response
        self.rate_limit_count: int = 0  # cuántas veces devolver 429 antes de OK
        self.request_count: int = 0

    def record_call(self, method: str, path: str, body: dict) -> None:
        self.call_log.append({"method": method, "path": path, "body": body})
        self.request_count += 1

    def maybe_rate_limit(self) -> Optional[dict]:
        if self.rate_limit_count > 0:
            self.rate_limit_count -= 1
            return {"_status": 429, "_body": {"code": "rate_limited",
                                              "message": "Too many requests"}}
        return None


def make_handler(state: MockState) -> Callable:
    """Crea una clase handler con el state cerrado."""

    class MockHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass  # Silenciar logs.

        def _send_json(self, body: dict, status: int = 200) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if not length:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}

        def do_GET(self) -> None:
            state.record_call("GET", self.path, {})
            if "/databases/" in self.path and self.path.endswith(self.path.split("/")[-1]):
                db_id = self.path.split("/")[-1]
                return self._send_json({
                    "id": db_id,
                    "properties": {n: {"type": "rich_text"} for n in state.database_properties},
                })
            if "/blocks/" in self.path and "/children" in self.path:
                block_id = self.path.split("/blocks/")[1].split("/")[0]
                return self._send_json({"results": []})
            self._send_json({"error": "not_found"}, status=404)

        def do_POST(self) -> None:
            body = self._read_body()
            state.record_call("POST", self.path, body)
            rl = state.maybe_rate_limit()
            if rl:
                self.send_response(rl["_status"])
                data = json.dumps(rl["_body"]).encode("utf-8")
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            if self.path.endswith("/query"):
                # Buscar page por notemartin_note_id.
                note_id = (body.get("filter", {}).get("rich_text", {}).get("equals", ""))
                page_id = state.page_by_note.get(note_id)
                if page_id:
                    return self._send_json({"results": [{"id": page_id}]})
                return self._send_json({"results": []})

            if self.path == "/search":
                query = body.get("query", "")
                results = []
                for note_id, page_id in state.page_by_note.items():
                    if query.strip("[]") == note_id:
                        results.append({"id": page_id,
                                        "properties": {"title": {"title": [
                            {"plain_text": f"[{note_id}] test"}]}}})
                return self._send_json({"results": results})

            if self.path == "/pages":
                note_id = (body.get("properties", {}).get("notemartin_note_id", {})
                           .get("rich_text", [{}])[0].get("text", {}).get("content", ""))
                page_id = f"mock-page-{len(state.pages) + 1}"
                page_obj = {
                    "id": page_id,
                    "object": "page",
                    "properties": body.get("properties", {}),
                }
                state.pages[page_id] = page_obj
                if note_id:
                    state.page_by_note[note_id] = page_id
                return self._send_json(page_obj, status=200)

            self._send_json({"error": "not_found"}, status=404)

        def do_PATCH(self) -> None:
            body = self._read_body()
            state.record_call("PATCH", self.path, body)
            rl = state.maybe_rate_limit()
            if rl:
                self.send_response(rl["_status"])
                data = json.dumps(rl["_body"]).encode("utf-8")
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            if "/pages/" in self.path:
                page_id = self.path.split("/pages/")[1]
                if page_id in state.pages:
                    state.pages[page_id]["properties"].update(
                        body.get("properties", {})
                    )
                return self._send_json(state.pages.get(page_id, {"id": page_id}))

            if "/blocks/" in self.path and "/children" in self.path:
                block_id = self.path.split("/blocks/")[1].split("/")[0]
                return self._send_json({"results": [{"id": f"{block_id}-child"}]})

            self._send_json({"error": "not_found"}, status=404)

        def do_DELETE(self) -> None:
            state.record_call("DELETE", self.path, {})
            return self._send_json({"archived": True})

    return MockHandler


def start_server(state: MockState, host: str = "127.0.0.1", port: int = 0
                 ) -> tuple[HTTPServer, int]:
    """Inicia el server; devuelve (server, port)."""
    handler = make_handler(state)
    server = HTTPServer((host, port), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, port


def stop_server(server: HTTPServer) -> None:
    server.shutdown()
    server.server_close()


if __name__ == "__main__":
    # Demo: arrancar y mostrar URL.
    state = MockState()
    server, port = start_server(state)
    print(f"Mock Notion server en http://127.0.0.1:{port}")
    try:
        import time
        time.sleep(2)
    finally:
        stop_server(server)
