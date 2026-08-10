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
import html
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from loguru import logger

from th_cli.config import config

# HTTP Endpoints
ENDPOINT_ROOT = "/"
ENDPOINT_LOGS_STREAM = "/api/logs/stream"


class LogStreamingHandler(BaseHTTPRequestHandler):
    """HTTP handler for streaming log data in real-time."""

    def do_GET(self):
        """Handle GET requests for log streaming."""
        if self.path == ENDPOINT_ROOT:
            self.serve_log_viewer()
        elif self.path == ENDPOINT_LOGS_STREAM:
            self.stream_logs()
        else:
            logger.warning(f"404 for GET {self.path}")
            self.send_error(404)
    
    def stream_logs(self):
        """Stream logs using Server-Sent Events (SSE)."""
        logger.info("Client connected for log stream")
        
        # Send SSE headers
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Get the log queue from the server
        log_queue = getattr(self.server, "log_queue", None)
        if not log_queue:
            logger.error("No log queue found on server for streaming")
            return

        logger.info("Starting to stream logs to client via SSE")
        sent_count = 0
        client_disconnected = False
        
        try:
            # Send initial connection message
            if not self._send_sse_event("connected", {"message": "Log stream connected"}):
                logger.debug("Client disconnected during initial connection")
                return
            
            while not client_disconnected:
                try:
                    # Get log entry from queue with timeout
                    log_entry = log_queue.get(timeout=1.0)
                    
                    if log_entry is None:  # Signal to stop
                        logger.info("Received end-of-stream signal for logs")
                        self._send_sse_event("end", {"message": "Log stream ended"})
                        break

                    # Send log entry as SSE event
                    if not self._send_sse_event("log", log_entry):
                        logger.debug("Client disconnected while streaming")
                        client_disconnected = True
                        break
                        
                    sent_count += 1
                    
                    if sent_count % 100 == 0:
                        logger.debug(f"Sent {sent_count} log entries to client")

                except queue.Empty:
                    # Send keepalive to prevent connection timeout
                    if not self._send_sse_event("keepalive", {"timestamp": time.time()}):
                        logger.debug("Client disconnected during keepalive")
                        client_disconnected = True
                        break
                    continue
                except Exception as e:
                    logger.debug(f"Error streaming log: {e}")
                    break

        except BrokenPipeError:
            logger.debug("Client disconnected (broken pipe)")
        except Exception as e:
            logger.debug(f"Log streaming error: {e}")

        logger.info(f"Log stream ended, total entries sent: {sent_count}")

    def _send_sse_event(self, event_type: str, data: dict) -> bool:
        """Send a Server-Sent Event.
        
        Returns:
            True if event was sent successfully, False if client disconnected
        """
        try:
            event_data = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            self.wfile.write(event_data.encode('utf-8'))
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Client disconnected - this is normal, not an error
            return False
        except Exception as e:
            logger.debug(f"Error sending SSE event: {e}")
            return False

    def serve_log_viewer(self):
        """Serve the log viewer HTML page."""
        # Get configuration from server
        test_run_title = getattr(self.server, "test_run_title", "Test Execution")
        run_id = getattr(self.server, "run_id", None)

        # config.hostname is only meaningful to the download link when it's a
        # real, routable address. This page can be opened from a different
        # device than the one running the CLI (that's why this server binds
        # to the LAN IP in the first place) - if config.hostname is just
        # "localhost" (the common case when the CLI and backend run on the
        # same machine as each other), embedding it here would tell a remote
        # browser to download from *itself*. Leave it unset in that case so
        # the page falls back to whatever host the browser actually used to
        # reach it (correct whenever the CLI and backend share a machine,
        # which is the common case); keep it when it's a real configured
        # address (correct when the CLI talks to a genuinely separate
        # backend host).
        backend_host = None if config.hostname in ("localhost", "127.0.0.1") else config.hostname

        # Read HTML template from file
        try:
            template_path = Path(__file__).parent / "log_viewer.html"
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()

            # Replace placeholders
            html_content = html_template.format(
                test_run_title=html.escape(test_run_title),
                run_id=json.dumps(run_id),
                backend_host=json.dumps(backend_host),
            )
        except Exception as e:
            logger.error(f"Failed to load HTML template: {e}")
            # Fallback to simple HTML
            html_content = f"""
            <html>
            <head><title>Log Viewer Error</title></head>
            <body>
                <h1>Error loading log viewer interface</h1>
                <p>Template error: {html.escape(str(e))}</p>
                <p>Test Run: {html.escape(test_run_title)}</p>
            </body>
            </html>
            """

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        # Prevent caching
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("ETag", f'"{int(time.time())}"')
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress HTTP access logs to avoid clutter."""
        pass


class LogsHTTPServer:
    """Manages HTTP server for real-time log streaming."""

    def __init__(self, port: int = 8998):
        """Initialize the logs HTTP server.
        
        Args:
            port: Port number for the HTTP server (default: 8998)
        """
        self.port = port
        self.server: Optional[ThreadingHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start(
        self,
        log_queue: queue.Queue,
        test_run_title: str = "Test Execution",
        local_ip: Optional[str] = None,
    ):
        """Start HTTP server for log streaming.

        Args:
            log_queue: Queue containing log entries to stream
            test_run_title: Title of the test run for display
            local_ip: Local IP address for display (defaults to localhost)
        """
        try:
            # Use ThreadingHTTPServer for better concurrency
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), LogStreamingHandler)
            self.server.allow_reuse_address = True

            # Set required attributes on the server
            self.server.log_queue = log_queue
            self.server.test_run_title = test_run_title
            self.server.local_ip = local_ip or "localhost"
            self.server.run_id = None

            logger.info(f"Logs HTTP server configured for test run: {test_run_title}")

            def run_server():
                logger.info(f"Starting logs HTTP server on port {self.port}")
                try:
                    self.server.serve_forever()
                except Exception as e:
                    logger.error(f"Logs HTTP server error: {e}")

            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            logger.info(f"Logs HTTP server thread started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start logs HTTP server: {e}")
            raise

    def set_run_id(self, run_id: int) -> None:
        """Set the run id the "Download Logs" link should point to, once the
        run has been created (it doesn't exist yet when the server starts).
        """
        if self.server is not None:
            self.server.run_id = run_id

    def stop(self):
        """Stop HTTP server."""
        if self.server:
            try:
                self.server.shutdown()
                logger.info("Logs HTTP server stopped")
            except Exception as e:
                logger.debug(f"Error stopping logs HTTP server: {e}")
            finally:
                self.server = None
                self.server_thread = None
