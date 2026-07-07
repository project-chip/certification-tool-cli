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
import copy
import datetime
import html
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from loguru import logger

# HTTP Endpoints
ENDPOINT_ROOT = "/"
ENDPOINT_LOGS_STREAM = "/api/logs/stream"
ENDPOINT_DOWNLOAD_LOGS = "/download_logs"
ENDPOINT_STATUS = "/api/status"


class LogStreamingHandler(BaseHTTPRequestHandler):
    """HTTP handler for streaming log data in real-time."""

    def do_GET(self):
        """Handle GET requests for log streaming."""
        if self.path == ENDPOINT_ROOT:
            self.serve_log_viewer()
        elif self.path == ENDPOINT_LOGS_STREAM:
            self.stream_logs()
        elif self.path == ENDPOINT_DOWNLOAD_LOGS:
            self.download_logs()
        elif self.path == ENDPOINT_STATUS:
            self.serve_status()
        else:
            logger.warning(f"404 for GET {self.path}")
            self.send_error(404)

    def serve_status(self):
        """Return current run title and start time as JSON (used for new-execution detection)."""
        status = {
            "run_title": getattr(self.server, "test_run_title", ""),
            "start_time": getattr(self.server, "start_time", ""),
        }
        body = json.dumps(status).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def download_logs(self):
        """Serve the log file for download using chunked streaming."""
        log_file_path = getattr(self.server, "log_file_path", None)

        if not log_file_path or not Path(log_file_path).exists():
            self.send_error(404, "Log file not found")
            return

        try:
            file_path = Path(log_file_path)
            filename = file_path.name
            file_size = file_path.stat().st_size

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(file_size))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            CHUNK_SIZE = 65536  # 64 KB
            bytes_sent = 0
            with open(log_file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    self.wfile.write(chunk)
                    bytes_sent += len(chunk)

            logger.info(f"Log file downloaded: {filename} ({bytes_sent} bytes)")

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Client disconnected during download - normal, not an error
            logger.debug("Client disconnected during log file download")
        except Exception as e:
            logger.error(f"Error serving log file: {e}")

    def stream_logs(self):
        """Stream logs (and tree events) using Server-Sent Events (SSE)."""
        logger.info("Client connected for log stream")

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Create a per-client queue and register it in the broadcast set.
        # Each SSE client owns its own queue so events are never stolen between connections.
        client_queue: queue.Queue = queue.Queue(maxsize=500)
        active_clients = getattr(self.server, "active_clients", None)
        clients_lock = getattr(self.server, "clients_lock", None)
        if active_clients is None or clients_lock is None:
            logger.error("No active_clients/clients_lock found on server")
            return
        with clients_lock:
            active_clients.add(client_queue)

        # Send initial connection event.
        if not self._send_sse_event("connected", {"message": "Log stream connected"}):
            with clients_lock:
                active_clients.discard(client_queue)
            return

        # Send current tree snapshot if available — covers reconnecting clients
        # that arrive after init_tree() was called.
        tree_state: dict = getattr(self.server, "tree_state", {})
        tree_lock = getattr(self.server, "tree_lock", None)
        sent_tree_snapshot = False
        if tree_state:
            if tree_lock:
                with tree_lock:
                    tree_copy = copy.deepcopy(tree_state)
            else:
                tree_copy = copy.deepcopy(tree_state)
            if not self._send_sse_event("tree_init", tree_copy):
                with clients_lock:
                    active_clients.discard(client_queue)
                return
            sent_tree_snapshot = True

        logger.info("Starting to stream events to client via SSE")
        sent_count = 0
        client_disconnected = False

        try:
            while not client_disconnected:
                try:
                    entry = client_queue.get(timeout=1.0)
                except queue.Empty:
                    if not self._send_sse_event("keepalive", {"timestamp": time.time()}):
                        client_disconnected = True
                    continue
                except Exception as e:
                    logger.debug(f"Queue read error: {e}")
                    break

                if entry is None:  # End-of-stream sentinel
                    self._send_sse_event("end", {"message": "Log stream ended"})
                    break

                if not isinstance(entry, dict):
                    continue

                entry_type = entry.get("type", "log")

                if entry_type == "tree_init":
                    # Skip queue duplicate if we already sent the snapshot on connect.
                    if sent_tree_snapshot:
                        continue
                    if not self._send_sse_event("tree_init", entry.get("data", entry)):
                        client_disconnected = True
                    else:
                        sent_tree_snapshot = True

                elif entry_type == "tree_update":
                    if not self._send_sse_event("tree_update", entry):
                        client_disconnected = True

                else:
                    # Regular log entry (no "type" key, or type=="log").
                    if not self._send_sse_event("log", entry):
                        client_disconnected = True
                    else:
                        sent_count += 1
                        if sent_count % 100 == 0:
                            logger.debug(f"Sent {sent_count} log entries to client")

        except BrokenPipeError:
            logger.debug("Client disconnected (broken pipe)")
        except Exception as e:
            logger.debug(f"Log streaming error: {e}")
        finally:
            with clients_lock:
                active_clients.discard(client_queue)

        logger.info(f"Log stream ended, total log entries sent: {sent_count}")

    def _send_sse_event(self, event_type: str, data: dict) -> bool:
        """Send a Server-Sent Event.

        Returns True if sent successfully, False if the client disconnected.
        """
        try:
            event_data = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            self.wfile.write(event_data.encode("utf-8"))
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return False
        except Exception as e:
            logger.debug(f"Error sending SSE event: {e}")
            return False

    def serve_log_viewer(self):
        """Serve the log viewer HTML page."""
        # Get configuration from server
        test_run_title = getattr(self.server, "test_run_title", "Test Execution")
        
        # Read HTML template from file
        try:
            template_path = Path(__file__).parent / "log_viewer.html"
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()

            html_content = html_template.format(test_run_title=html.escape(test_run_title))
        except Exception as e:
            logger.error(f"Failed to load HTML template: {e}")
            html_content = f"""
            <html><head><title>Log Viewer Error</title></head>
            <body><h1>Error loading log viewer</h1><p>{html.escape(str(e))}</p></body></html>
            """

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("ETag", f'"{int(time.time())}"')
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default HTTP access log output."""
        pass


class LogsHTTPServer:
    """Manages the HTTP server for real-time log streaming."""

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
        active_clients: set,
        clients_lock: threading.Lock,
        tree_state: dict,
        test_run_title: str = "Test Execution",
        local_ip: Optional[str] = None,
        log_file_path: Optional[str] = None,
        tree_lock: Optional[threading.Lock] = None,
    ):
        """Start the HTTP server for log streaming.

        Args:
            active_clients: Shared set of per-client queues; broadcast puts into all of them.
            clients_lock: Lock protecting active_clients mutations.
            tree_state: Mutable dict shared with LogStreamHandler; mutated in-place
                so clients connecting after init_tree() receive a current snapshot.
            test_run_title: Title shown in the browser UI.
            local_ip: LAN IP used for display purposes.
            log_file_path: Path to the on-disk log file for download.
            tree_lock: Lock protecting tree_state reads/writes.
        """
        try:
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), LogStreamingHandler)
            self.server.allow_reuse_address = True

            self.server.active_clients = active_clients
            self.server.clients_lock = clients_lock
            self.server.tree_state = tree_state  # shared reference — mutated externally
            self.server.tree_lock = tree_lock
            self.server.test_run_title = test_run_title
            self.server.local_ip = local_ip or "localhost"
            self.server.log_file_path = log_file_path
            self.server.start_time = datetime.datetime.now().isoformat()

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

    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            try:
                self.server.shutdown()
                logger.info("Logs HTTP server stopped")
            except Exception as e:
                logger.debug(f"Error stopping logs HTTP server: {e}")
            finally:
                self.server = None
                self.server_thread = None
