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
import base64
import html
import json
import queue
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx
from loguru import logger

# HTTP Endpoints
ENDPOINT_ROOT = "/"
ENDPOINT_VIDEO_LIVE = "/video_live.mp4"
ENDPOINT_SUBMIT_RESPONSE = "/submit_response"
ENDPOINT_API_STREAMS = "/api/streams"
ENDPOINT_API_STREAM_PROXY = "/api/stream_proxy"

# Timeout constants (in seconds)
PUSH_AV_STREAMS_TIMEOUT = 5.0  # Timeout for fetching stream list
PUSH_AV_PROXY_TIMEOUT = 30.0  # Timeout for proxying stream data


class VideoStreamingHandler(BaseHTTPRequestHandler):
    """HTTP handler for streaming video data and handling user responses."""

    def do_GET(self):
        logger.info(f"GET request received: {self.path}")

        # Parse URL to strip query parameters for routing
        parsed_url = urlparse(self.path)
        path_only = parsed_url.path

        if path_only == ENDPOINT_VIDEO_LIVE:
            self.stream_live_video()
        elif path_only == ENDPOINT_ROOT:
            self.serve_player()
        elif path_only == ENDPOINT_API_STREAMS:
            self.handle_streams_api()
        elif path_only.startswith(ENDPOINT_API_STREAM_PROXY):
            self.handle_stream_proxy()
        elif path_only.startswith("/proxy/"):
            # New simplified proxy endpoint: /proxy/<base64_encoded_url>
            self.handle_simple_proxy()
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

    def handle_streams_api(self):
        """Fetch and return available streams from Push AV Server."""
        try:
            push_av_server_url = getattr(self.server, "push_av_server_url", None)

            if not push_av_server_url:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b'{"error": "Push AV Server URL not configured"}')
                return

            # Fetch streams from Push AV Server
            # Disable SSL verification for self-signed certificates in test environments.
            # Push AV Servers typically use self-signed certificates. This is acceptable
            # since we're connecting to test devices in controlled lab settings, similar
            # to how browsers prompt users to accept self-signed certificates in the TH web UI.
            with httpx.Client(verify=False, timeout=PUSH_AV_STREAMS_TIMEOUT) as client:
                response = client.get(f"{push_av_server_url}/streams")

                if response.status_code == 200:
                    streams_data = response.json()

                    # Send successful response
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(streams_data).encode())
                else:
                    raise Exception(f"Server returned {response.status_code}")

        except Exception as e:
            logger.error(f"Error fetching streams: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "streams": []}).encode())

    def handle_simple_proxy(self):
        """Simplified proxy that accepts base64-encoded URLs in the path.

        Format: /proxy/<base64_url>/<additional_path>
        This allows dash.js to append paths naturally.
        """
        try:
            # Extract path after /proxy/
            path_after_proxy = self.path[len("/proxy/") :]

            # Split to get base64 URL and any additional path
            parts = path_after_proxy.split("/", 1)
            encoded_base = parts[0]
            extra_path = "/" + parts[1] if len(parts) > 1 else ""

            # Decode base URL
            try:
                base_url = base64.urlsafe_b64decode(encoded_base.encode()).decode("utf-8")
            except Exception as e:
                logger.error(f"Failed to decode base64 URL: {e}")
                self.send_error(400, "Invalid encoded URL")
                return

            # Construct full URL
            stream_url = base_url.rstrip("/") + extra_path

            # Fetch from upstream
            # Disable SSL verification for self-signed certificates in test environments.
            # Push AV Servers typically use self-signed certificates. This is acceptable
            # since we're connecting to test devices in controlled lab settings, similar
            # to how browsers prompt users to accept self-signed certificates in the TH web UI.
            with httpx.Client(verify=False, timeout=PUSH_AV_PROXY_TIMEOUT) as client:
                try:
                    response = client.get(stream_url)
                except Exception as e:
                    logger.error(f"Failed to fetch {stream_url}: {e}")
                    self.send_error(500, f"Upstream fetch error: {str(e)}")
                    return

                if response.status_code != 200:
                    logger.warning(f"Upstream returned {response.status_code} for {stream_url}")
                    # Return the same status code from upstream (404, 403, etc.)
                    self.send_error(response.status_code, f"Upstream returned {response.status_code}")
                    return

                content_type = response.headers.get("Content-Type", "application/octet-stream")

                # Send response
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Access-Control-Allow-Origin", "*")

                content_length = response.headers.get("Content-Length")
                if content_length:
                    self.send_header("Content-Length", content_length)

                self.end_headers()
                self.wfile.write(response.content)

        except Exception as e:
            logger.error(f"Error in simple proxy: {e}", exc_info=True)
            if not self.wfile.closed:
                self.send_error(500, f"Proxy error: {str(e)}")

    def handle_stream_proxy(self):
        """Proxy video stream from Push AV Server to avoid CORS and SSL issues."""
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            stream_url = query_params.get("url", [None])[0]

            if not stream_url:
                self.send_error(400, "Missing 'url' parameter")
                return

            # Check if there's additional path after /api/stream_proxy
            path = parsed_url.path
            if path.startswith("/api/stream_proxy/"):
                extra_path = path[len("/api/stream_proxy") :]
                stream_url = stream_url.rstrip("/") + extra_path

            # Fetch from Push AV Server
            # Disable SSL verification for self-signed certificates in test environments.
            # Push AV Servers typically use self-signed certificates. This is acceptable
            # since we're connecting to test devices in controlled lab settings, similar
            # to how browsers prompt users to accept self-signed certificates in the TH web UI.
            with httpx.Client(verify=False, timeout=PUSH_AV_PROXY_TIMEOUT) as client:
                response = client.get(stream_url)

                if response.status_code != 200:
                    self.send_error(response.status_code, "Upstream error")
                    return

                content_type = response.headers.get("Content-Type", "video/mp4")

                # Check if this is an MPD manifest file
                if stream_url.endswith(".mpd") or "mpd" in content_type.lower():
                    # Rewrite DASH manifest URLs to use our proxy
                    content = response.text

                    # For DASH manifests, use simplified base64-encoded proxy
                    # This allows dash.js to naturally append paths for segment templates

                    # Extract base URL from stream_url (the directory containing the manifest)
                    base_url = "/".join(stream_url.rsplit("/", 1)[:-1])  # Remove filename

                    # Encode the base URL for use in proxy path
                    encoded_base = base64.urlsafe_b64encode(base_url.encode()).decode("ascii")

                    # Remove all existing BaseURL elements
                    content = re.sub(r"<BaseURL>[^<]+</BaseURL>", "", content)

                    # Get local IP and port from server configuration
                    local_ip = getattr(self.server, "local_ip", "localhost")
                    port = self.server.server_port

                    # Rewrite non-template attributes (like initialization)
                    def rewrite_media_url(match):
                        attr_name = match.group(1)
                        original_url = match.group(2)

                        # Skip template URLs - leave them as-is, BaseURL will handle them
                        if "$" in original_url:
                            return match.group(0)

                        # For non-template URLs, make them absolute
                        if original_url.startswith("http"):
                            full_url = original_url
                        else:
                            full_url = f"{base_url}/{original_url}"

                        # Use simple proxy format with dynamic host
                        encoded_url = base64.urlsafe_b64encode(full_url.encode()).decode("ascii")
                        proxied_url = f"http://{local_ip}:{port}/proxy/{encoded_url}"

                        return f'{attr_name}="{proxied_url}"'

                    content = re.sub(r'(initialization|sourceURL)="([^"]+)"', rewrite_media_url, content)

                    # Add BaseURL using the simplified proxy format with dynamic host
                    # dash.js will append media template paths to this
                    proxied_base = f"http://{local_ip}:{port}/proxy/{encoded_base}"

                    # Insert BaseURL at the beginning of the first Period
                    if "<Period>" in content:
                        content = content.replace("<Period>", f"<Period><BaseURL>{proxied_base}/</BaseURL>", 1)
                    elif "<MPD" in content:
                        # Insert after MPD opening tag
                        mpd_end = content.find(">", content.find("<MPD"))
                        if mpd_end > 0:
                            content = (
                                content[: mpd_end + 1]
                                + f"\n<BaseURL>{proxied_base}/</BaseURL>\n"
                                + content[mpd_end + 1 :]
                            )

                    # Send modified manifest
                    self.send_response(200)
                    self.send_header("Content-Type", "application/dash+xml")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(content.encode("utf-8"))))
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                else:
                    # Regular file - stream as-is
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Access-Control-Allow-Origin", "*")

                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        self.send_header("Content-Length", content_length)

                    self.end_headers()
                    self.wfile.write(response.content)

        except Exception as e:
            logger.error(f"Error proxying stream: {e}")
            if not self.wfile.closed:
                self.send_error(500, f"Proxy error: {str(e)}")

    def serve_player(self):
        """Serve a video player using external HTML template."""
        # Get dynamic data from server
        prompt_options = getattr(self.server, "prompt_options", {})
        prompt_text = getattr(self.server, "prompt_text", "Video Verification")
        is_push_av = getattr(self.server, "is_push_av_verification", False)
        push_av_server_url = getattr(self.server, "push_av_server_url", "https://localhost:1234")

        # Generate radio button options dynamically
        radio_options_html = ""
        for key, value in prompt_options.items():
            radio_options_html += f"""
            <div class="popup-radio-row" data-value="{value}" onclick="selectOption({value})">
                <input type="radio" name="option" value="{value}" id="radio_{value}">
                <label for="radio_{value}">{html.escape(key)}</label>
            </div>
            """

        # Choose template based on verification type
        if is_push_av:
            template_filename = "push_av_stream_verification.html"
        else:
            template_filename = "video_verification.html"

        # Read HTML template from file
        try:
            template_path = Path(__file__).parent / template_filename
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()

            # Replace placeholders
            if is_push_av:
                # Push AV template needs the server URL
                html_content = html_template.format(
                    prompt_text=html.escape(prompt_text),
                    radio_options_html=radio_options_html,
                    push_av_server_url=html.escape(push_av_server_url or "https://localhost:1234"),
                )
            else:
                # Regular video verification template doesn't need Push AV server URL
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
        # Aggressive cache prevention - multiple headers to bypass all browser caching
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Last-Modified", "0")

        # Add ETag to force browser to check for changes
        self.send_header("ETag", f'"{int(time.time())}"')
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

    def start(
        self,
        mp4_queue,
        response_queue,
        video_handler,
        prompt_options=None,
        prompt_text="Video Verification",
        is_push_av_verification=False,
        push_av_server_url=None,
        local_ip=None,
    ):
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
            self.server.is_push_av_verification = is_push_av_verification
            self.server.push_av_server_url = push_av_server_url
            self.server.local_ip = local_ip or "localhost"

            logger.info(f"HTTP server configured with prompt_options: {self.server.prompt_options}")
            logger.info(f"HTTP server configured with prompt_text: {self.server.prompt_text}")
            logger.info(f"HTTP server Push AV mode: {is_push_av_verification}")
            if push_av_server_url:
                logger.info(f"HTTP server Push AV Server URL: {push_av_server_url}")

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
