#
# Copyright (c) 2025 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import asyncio
import json
import queue
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from loguru import logger


def _get_local_ip() -> str:
    """Get the LAN IP of this machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


class TwoWayTalkHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the two-way talk verification page."""

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self._serve_page()
        elif self.path == "/prompt_ready":
            self._serve_prompt_ready()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/submit_response":
            self._handle_response()
        elif self.path == "/browser_ready":
            self._handle_browser_ready()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_page(self):
        prompt_ready = getattr(self.server, "prompt_ready", False)
        th_hostname = getattr(self.server, "th_hostname", "127.0.0.1")

        try:
            template_path = Path(__file__).parent / "two_way_talk_verification.html"
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            page = template.format(
                th_hostname=th_hostname,
                prompt_ready="true" if prompt_ready else "false",
            )
        except Exception as e:
            logger.error(f"Failed to load two-way talk HTML template: {e}")
            page = "<html><body><h1>Two-Way Talk Verification</h1>" f"<p>Template error: {e}</p></body></html>"

        encoded = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_prompt_ready(self):
        """JSON endpoint polled by the browser to know when the prompt is ready.
        When ready, also returns the prompt text and options so the browser can
        render radio buttons dynamically (avoids stale server-side HTML baked at
        page-load time when options were not yet set)."""
        ready = getattr(self.server, "prompt_ready", False)
        payload = {"ready": ready}
        if ready:
            payload["prompt_text"] = getattr(self.server, "prompt_text", "")
            payload["options"] = getattr(self.server, "prompt_options", {})
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _handle_response(self):
        try:
            if "Content-Length" not in self.headers:
                self.send_error(400, "Missing Content-Length")
                return
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            raw = data.get("response")
            if raw is None:
                raise ValueError("Missing 'response' key")
            value = int(raw)

            response_queue = getattr(self.server, "response_queue", None)
            if response_queue:
                response_queue.put_nowait(value)
            else:
                self.send_error(500, "No response queue")
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"TwoWayTalk response handler error: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(f'{{"error": "{e}"}}'.encode())

    def _handle_browser_ready(self):
        """Called by the browser page on load to signal the user has it open."""
        browser_event = getattr(self.server, "browser_ready_event", None)
        if browser_event:
            browser_event.set()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

    def log_message(self, format, *args):
        pass  # suppress HTTP access logs


# Module-level singletons
_active_handler: Optional["TwoWayTalkHandler"] = None
# Also keep a direct reference to the running HTTP server so show_prompt can be
# called even if the handler object reference is lost (e.g. module import edge cases).
_active_server: Optional["_ReuseAddrHTTPServer"] = None


def get_active_handler() -> Optional["TwoWayTalkHandler"]:
    return _active_handler


def set_active_handler(handler: Optional["TwoWayTalkHandler"]) -> None:
    global _active_handler
    _active_handler = handler


def show_prompt_on_active_server(prompt_text: str, prompt_options: dict) -> bool:
    """Call show_prompt on the currently running HTTP server regardless of handler state.
    Returns True if the server was found and updated, False otherwise."""
    if _active_server is not None:
        _active_server.prompt_text = prompt_text
        _active_server.prompt_options = prompt_options
        _active_server.prompt_ready = True
        logger.debug("TwoWayTalk prompt updated via module-level server reference")
        return True
    return False


class _ReuseAddrHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer with allow_reuse_address set before server_bind()."""

    allow_reuse_address = True


class TwoWayTalkHandler:
    """Manages the local HTTP server for two-way talk verification.

    Start with start_waiting() before the test begins — the browser connects
    as the WebRTC peer and shows the live session.  When step 8 arrives call
    show_prompt() to reveal the PASS/FAIL form in the browser.
    """

    def __init__(self, port: int = 8999):
        self.port = port
        self._server: Optional[ThreadingHTTPServer] = None
        self._response_queue: queue.Queue = queue.Queue()
        self._browser_ready_event: threading.Event = threading.Event()

    @staticmethod
    def _free_port(port: int) -> None:
        """Kill any process that is still listening on the given port."""
        import subprocess

        try:
            result = subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True,
            )
            if result.returncode == 0:
                logger.info(f"Freed port {port} from previous process")
                time.sleep(0.5)  # give the OS a moment to release the socket
        except FileNotFoundError:
            pass  # fuser not available on this platform

    def _start_server(self) -> None:
        """Bind and start the HTTP server thread.  Does NOT free the port first."""
        global _active_server
        self._server = _ReuseAddrHTTPServer(("0.0.0.0", self.port), TwoWayTalkHTTPHandler)
        self._server.prompt_text = "Verify two-way talk"
        self._server.prompt_options = {}
        self._server.prompt_ready = False
        self._server.response_queue = self._response_queue
        self._server.browser_ready_event = self._browser_ready_event
        self._server.th_hostname = _get_local_ip()

        t = threading.Thread(target=self._server.serve_forever, daemon=True)
        t.start()
        logger.info(f"TwoWayTalk HTTP server started on port {self.port}")
        _active_server = self._server
        set_active_handler(self)

    def start_waiting(self) -> None:
        """Start the HTTP server before the test.  Prompt is hidden until show_prompt().
        Kills any zombie process still holding the port first (safe to call before the
        server is bound — the current process does not hold the port yet)."""
        self._free_port(self.port)
        self._start_server()

    def start_server_only(self) -> None:
        """Start the HTTP server WITHOUT killing the port first.
        Use this when the current process may already be listening on the port
        (e.g. fallback path where start_waiting() was not called earlier)."""
        self._start_server()

    def wait_for_browser(self, timeout: float = 120.0) -> bool:
        """Block until the browser page loads and posts /browser_ready.
        Returns True if browser connected, False if timed out."""
        return self._browser_ready_event.wait(timeout=timeout)

    def show_prompt(self, prompt_text: str, prompt_options: dict) -> None:
        """Reveal the PASS/FAIL prompt in the browser (called at step 8)."""
        if self._server:
            self._server.prompt_text = prompt_text
            self._server.prompt_options = prompt_options
            self._server.prompt_ready = True
            logger.debug("TwoWayTalk prompt is now visible")

    # Keep backward-compat alias used by old prompt_manager code
    def start(self, prompt_text: str, prompt_options: dict) -> None:
        self.start_waiting()
        self.show_prompt(prompt_text, prompt_options)

    def update_prompt(self, prompt_text: str, prompt_options: dict) -> None:
        self.show_prompt(prompt_text, prompt_options)

    def stop(self) -> None:
        global _active_server
        set_active_handler(None)
        _active_server = None
        if self._server:
            try:
                self._server.shutdown()
            except Exception as e:
                logger.debug(f"Error stopping TwoWayTalk server: {e}")
            finally:
                self._server = None

    async def wait_for_user_response(self, timeout: float) -> Optional[int]:
        start = time.time()
        while time.time() - start < timeout:
            try:
                return self._response_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.1)
        logger.warning("TwoWayTalk user response timed out")
        return None
