"""Standalone Playwright-backed HTTP server for frontend/computer-use tasks.

Written into a sandbox by `SandboxEnvironment`/`DaytonaEnvironment` (see
`_BROWSER_SETUP_COMMAND` in `data_gen.sandbox_environment`) when
`enable_browser=True`, and run there as a background process (`python3
/opt/browser_driver.py &`) on a fixed local port. The agent then drives it
with plain `curl` bash commands - this keeps the environment's `.execute()`
contract (one bash command in, stdout/stderr out) completely unchanged, so
no changes are needed to the mini-swe-agent agent loop itself.

Endpoints (all on 127.0.0.1:8765, JSON in, text out):
    GET  /health              -> "ok" once the browser is ready
    POST /goto     {"url"}    -> "ok"
    POST /click    {"x","y"}  -> "ok"
    POST /scroll   {"dx","dy"}-> "ok"
    POST /screenshot           -> a `<MSWEA_MULTIMODAL_CONTENT>`-wrapped data
                                   URL (see
                                   `minisweagent.models.utils.openai_multimodal`),
                                   so a model configured with
                                   `multimodal_regex` set to
                                   `DEFAULT_MULTIMODAL_REGEX` sees the
                                   screenshot as an image content block
                                   rather than raw base64 text.

Runs headless - no Xvfb/X11 needed, since Playwright's screenshot/click/
scroll APIs operate against Chromium's own rendering surface over CDP.
"""

from __future__ import annotations

import base64
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from playwright.sync_api import sync_playwright

PORT = 8765

_playwright = sync_playwright().start()
_browser = _playwright.chromium.launch(headless=True)
_page = _browser.new_page(viewport={"width": 1280, "height": 800})
_page.goto("about:blank")


class Handler(BaseHTTPRequestHandler):
    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _respond(self, text: str, status: int = 200):
        payload = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self._respond("ok")
        else:
            self._respond("not found", 404)

    def do_POST(self):
        try:
            body = self._body()
            if self.path == "/goto":
                _page.goto(body["url"])
                self._respond("ok")
            elif self.path == "/click":
                _page.mouse.click(float(body["x"]), float(body["y"]))
                self._respond("ok")
            elif self.path == "/scroll":
                _page.mouse.wheel(float(body.get("dx", 0)), float(body.get("dy", 0)))
                self._respond("ok")
            elif self.path == "/screenshot":
                png_b64 = base64.b64encode(_page.screenshot()).decode()
                data_url = f"data:image/png;base64,{png_b64}"
                self._respond(
                    "<MSWEA_MULTIMODAL_CONTENT>"
                    "<CONTENT_TYPE>image_url</CONTENT_TYPE>"
                    f"{data_url}"
                    "</MSWEA_MULTIMODAL_CONTENT>"
                )
            else:
                self._respond("not found", 404)
        except Exception as e:  # noqa: BLE001 - reported to the calling curl, not raised
            self._respond(f"error: {e}", 500)

    def log_message(self, *args):  # silence default stderr access logging
        pass


if __name__ == "__main__":
    # Plain HTTPServer, not ThreadingHTTPServer: Playwright's sync API is
    # bound to whatever thread created _playwright/_browser/_page (main,
    # here) via greenlet - a threading server would dispatch each request
    # to a new worker thread and every browser call would fail with
    # "Cannot switch to a different thread". Single-threaded means requests
    # are handled sequentially, which is fine - a solving agent only ever
    # issues one action at a time anyway.
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
