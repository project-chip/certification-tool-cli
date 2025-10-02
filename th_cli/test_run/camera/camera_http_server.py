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
import html
import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from loguru import logger

from th_cli.th_utils.ffmpeg_converter import CHUNK_SIZE

# HTTP Endpoints
ENDPOINT_ROOT = "/"
ENDPOINT_VIDEO_LIVE = "/video_live.mp4"
ENDPOINT_SUBMIT_RESPONSE = "/submit_response"


class VideoStreamingHandler(BaseHTTPRequestHandler):
    """HTTP handler for streaming video data and handling user responses."""

    def do_GET(self):
        logger.info(f"GET request received: {self.path}")
        if self.path == ENDPOINT_VIDEO_LIVE:
            self.stream_live_video()
        elif self.path == ENDPOINT_ROOT:
            self.serve_player()
        else:
            logger.warning(f"404 for GET {self.path}")
            self.send_error(404)

    def do_POST(self):
        logger.info(f"POST request received: {self.path}")
        if self.path == ENDPOINT_SUBMIT_RESPONSE:
            self.handle_response()
        else:
            logger.warning(f"404 for POST {self.path}")
            self.send_error(404)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def stream_live_video(self):
        """Stream live video data as HTTP response during capture."""
        logger.info("HTTP client connected for LIVE video stream")
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        # Get the MP4 queue from the server (converted data)
        mp4_queue = getattr(self.server, "mp4_queue", None)
        if not mp4_queue:
            logger.error("No MP4 queue found on server for live stream")
            return

        logger.info("Starting to stream LIVE MP4 data to HTTP client")
        bytes_sent = 0
        try:
            while True:
                try:
                    # Get converted MP4 data from queue
                    data = mp4_queue.get(timeout=1.0)
                    if data is None:  # Signal to stop
                        logger.info("Received end-of-stream signal")
                        break

                    self.wfile.write(data)
                    self.wfile.flush()
                    bytes_sent += len(data)
                    logger.debug(f"Sent {len(data)} bytes MP4 to HTTP client (total: {bytes_sent})")

                except queue.Empty:
                    logger.debug("No MP4 data in queue, continuing...")
                    continue
                except Exception as e:
                    logger.debug(f"Error streaming MP4: {e}")
                    break

        except Exception as e:
            logger.error(f"LIVE MP4 streaming error: {e}")

        logger.info(f"HTTP LIVE MP4 stream ended, total bytes sent: {bytes_sent}")

    def handle_response(self):
        """Handle user response from web UI."""
        logger.info(f"Received POST request to {self.path}")
        try:
            # Check if Content-Length header exists
            if "Content-Length" not in self.headers:
                logger.error("Missing Content-Length header")
                self.send_error(400, "Missing Content-Length header")
                return

            content_length = int(self.headers["Content-Length"])
            logger.info(f"Reading {content_length} bytes from request body")

            post_data = self.rfile.read(content_length)
            logger.info(f"Raw POST data: {post_data}")

            response_data = json.loads(post_data.decode("utf-8"))
            logger.info(f"Parsed JSON data: {response_data}")

            # Check if response key exists and is not None
            raw_response = response_data.get("response")
            if raw_response is None:
                raise ValueError("Missing 'response' key in JSON payload")

            response_value = int(raw_response)
            logger.info(f"Extracted response value: {response_value}")

            # Send response to the response queue
            response_queue = getattr(self.server, "response_queue", None)
            if response_queue:
                try:
                    response_queue.put_nowait(response_value)
                    logger.info(f"Response {response_value} queued successfully")
                except queue.Full:
                    logger.error("Response queue is full")
                    self.send_error(500, "Response queue is full")
                    return
            else:
                logger.error("No response queue found on server")
                self.send_error(500, "No response queue available")
                return

            # Send success response
            logger.info("Sending success response to client")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            response_json = '{"status": "success"}'
            self.wfile.write(response_json.encode())
            logger.info("Success response sent")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(f'{{"error": "Invalid JSON: {str(e)}"}}'.encode())
        except ValueError as e:
            logger.error(f"Value error: {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(f'{{"error": "Invalid response value: {str(e)}"}}'.encode())
        except Exception as e:
            logger.error(f"Unexpected error handling response: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(f'{{"error": "Server error: {str(e)}"}}'.encode())

    def serve_player(self):
        """Serve a video player using external HTML template."""
        # Get dynamic data from server
        prompt_options = getattr(self.server, "prompt_options", {})
        prompt_text = getattr(self.server, "prompt_text", "Video Verification")

        # Generate radio button options dynamically
        radio_options_html = ""
        for key, value in prompt_options.items():
            radio_options_html += f"""
            <div class="popup-radio-row" data-value="{value}" onclick="selectOption({value})">
                <input type="radio" id="radio_{value}" name="group_1" value="{value}">
                <label for="radio_{value}">{html.escape(key)}</label>
            </div>
            """

        # Read HTML template from file
        try:
            template_path = Path(__file__).parent / "video_verification.html"
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()

            # Replace placeholders
            html_content = html_template.format(
                prompt_text=html.escape(prompt_text), radio_options_html=radio_options_html
            )
        except Exception as e:
            logger.error(f"Failed to load HTML template: {e}")
            # Fallback to simple HTML
            html_content = f"""
            <html>
            <head><title>Video Verification Error</title></head>
            <body>
                <h1>Error loading video verification interface</h1>
                <p>Template error: {e}</p>
                <p>Prompt: {html.escape(prompt_text)}</p>
                <p>Options: {prompt_options}</p>
            </body>
            </html>
            """

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress HTTP logs
        pass


class CameraHTTPServer:
    """Manages HTTP server for video streaming and user interaction."""

    def __init__(self, port: int = 8999):
        self.port = port
        self.server: Optional[ThreadingHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start(self, mp4_queue, response_queue, video_handler, prompt_options=None, prompt_text="Video Verification"):
        """Start HTTP server with required queues and data."""
        try:
            # Use ThreadingHTTPServer for better concurrency
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), VideoStreamingHandler)
            self.server.allow_reuse_address = True

            # Set all required attributes on the server
            self.server.mp4_queue = mp4_queue
            self.server.response_queue = response_queue
            self.server.prompt_options = prompt_options or {}
            self.server.prompt_text = prompt_text
            self.server.video_handler = video_handler

            logger.info(f"HTTP server configured with prompt_options: {self.server.prompt_options}")
            logger.info(f"HTTP server configured with prompt_text: {self.server.prompt_text}")

            def run_server():
                logger.info(f"Starting HTTP video server on port {self.port}")
                try:
                    self.server.serve_forever()
                except Exception as e:
                    logger.error(f"HTTP server error: {e}")

            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            logger.info(f"HTTP server thread started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            raise

    def stop(self):
        """Stop HTTP server."""
        if self.server:
            try:
                self.server.shutdown()
                logger.info("HTTP server stopped")
            except Exception as e:
                logger.debug(f"Error stopping HTTP server: {e}")
            finally:
                self.server = None
                self.server_thread = None
