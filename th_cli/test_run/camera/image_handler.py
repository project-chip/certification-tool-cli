#
# Copyright (c) 2026 Project CHIP Authors
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
import html
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from loguru import logger


class ImageVerificationHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for serving a snapshot image and collecting user pass/fail response."""

    def do_GET(self):
        if self.path == "/":
            self._serve_page()
        elif self.path == "/image":
            self._serve_image()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/submit_response":
            self._handle_response()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_image(self):
        image_data = getattr(self.server, "image_data", None)
        if not image_data:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(image_data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(image_data)

    def _serve_page(self):
        prompt_text = getattr(self.server, "prompt_text", "Verify the snapshot image")
        prompt_options = getattr(self.server, "prompt_options", {})

        radio_options_html = ""
        for key, value in prompt_options.items():
            safe_value = int(value)
            radio_options_html += f"""
            <div class="popup-radio-row" data-value="{safe_value}" onclick="selectOption({safe_value})">
                <input type="radio" name="option" value="{safe_value}" id="radio_{safe_value}">
                <label for="radio_{safe_value}">{html.escape(key)}</label>
            </div>
            """

        try:
            template_path = Path(__file__).parent / "image_verification.html"
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()
            page = html_template.format(
                prompt_text=html.escape(prompt_text),
                radio_options_html=radio_options_html,
            )
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Failed to load image verification HTML template: {e}")
            page = f"<html><body><h1>Error loading template</h1><p>{e}</p></body></html>"

        encoded = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(encoded)

    def _handle_response(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))
            response_value = int(data["response"])

            response_queue = getattr(self.server, "response_queue", None)
            if response_queue:
                response_queue.put_nowait(response_value)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Malformed request body: {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Invalid JSON: {e}"}).encode())
        except KeyError as e:
            logger.error(f"Missing required field in request: {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Missing field: {e}"}).encode())
        except ValueError as e:
            logger.error(f"Invalid value in request: {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Invalid value: {e}"}).encode())
        except Exception as e:
            logger.error(f"Unexpected error handling image verification response: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


class ImageVerificationHandler:
    """Serves a snapshot image via HTTP and waits for user pass/fail response."""

    def __init__(self, port: int = 8999):
        self.port = port
        self.http_server: Optional[ThreadingHTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._response_queue: queue.Queue = queue.Queue()

    def set_prompt_data(self, prompt_text: str, options: dict, image_data: bytes):
        self._prompt_text = prompt_text
        self._options = options
        self._image_data = image_data

    async def start_image_server(self):
        """Start the HTTP server to serve the image page."""
        server = ThreadingHTTPServer(("0.0.0.0", self.port), ImageVerificationHTTPHandler)
        server.allow_reuse_address = True
        server.image_data = self._image_data
        server.prompt_text = getattr(self, "_prompt_text", "Verify the snapshot image")
        server.prompt_options = getattr(self, "_options", {})
        server.response_queue = self._response_queue
        server.port = self.port
        self.http_server = server

        def _run():
            logger.info(f"Image verification HTTP server starting on port {self.port}")
            try:
                self.http_server.serve_forever()
            except Exception as e:
                logger.error(f"Image HTTP server error: {e}")

        self._server_thread = threading.Thread(target=_run, daemon=True)
        self._server_thread.start()
        logger.info(f"Image verification server started on port {self.port}")

    async def wait_for_user_response(self, timeout: float) -> Optional[int]:
        """Wait for user response from the web UI."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return self._response_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.1)
        logger.warning("Image verification response timed out")
        return None

    def stop_image_server(self):
        """Stop the HTTP server."""
        if self.http_server:
            try:
                self.http_server.shutdown()
            except Exception as e:
                logger.debug(f"Error stopping image HTTP server: {e}")
            finally:
                self.http_server = None
                self._server_thread = None
