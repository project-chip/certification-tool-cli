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
import datetime
import queue
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from .camera_http_server import CameraHTTPServer
from .webrtc_session import CLIWebRTCSession
from .websocket_manager import VideoWebSocketManager


class CameraStreamHandler:
    """Main coordinator for camera streaming functionality."""

    def __init__(self, output_dir: Optional[str] = None, use_webrtc: bool = True):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.websocket_manager = VideoWebSocketManager()
        self.webrtc_session: Optional[CLIWebRTCSession] = None
        self.use_webrtc = use_webrtc  # Try WebRTC first for camera tests
        self.http_server = CameraHTTPServer()

        # State
        self.current_stream_file: Optional[Path] = None
        self.mp4_queue = queue.Queue()  # Converted MP4 data for live streaming
        self.response_queue = queue.Queue()  # User responses from web UI
        self.prompt_options = {}  # Store prompt options
        self.prompt_text = ""  # Store prompt text

        # Stream readiness signaling
        self.stream_ready_event = asyncio.Event()

    def set_prompt_data(self, prompt_text: str, options: dict):
        """Set prompt text and options for the web UI."""
        self.prompt_text = prompt_text
        self.prompt_options = options
        logger.info(f"Set prompt options: {options}")

    async def start_video_capture_and_stream(self, prompt_id: str) -> Path:
        """Start capturing video stream to file AND serve via HTTP."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_verification_{prompt_id}_{timestamp}.bin"
        self.current_stream_file = self.output_dir / filename

        logger.info(f"Starting video capture to: {self.current_stream_file}")

        # Reset the stream ready event
        self.stream_ready_event.clear()

        # Start HTTP server with current prompt data
        self.http_server.start(
            mp4_queue=self.mp4_queue,
            response_queue=self.response_queue,
            video_handler=self,
            prompt_options=self.prompt_options,
            prompt_text=self.prompt_text,
        )

        # Start background task for video capture
        asyncio.create_task(self._initialize_video_capture())

        return self.current_stream_file

    async def wait_for_stream_ready(self, timeout: float = 10.0) -> bool:
        """Wait for the video stream to be ready for viewing."""
        try:
            await asyncio.wait_for(self.stream_ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Stream readiness timeout after {timeout}s")
            return False

    async def _initialize_video_capture(self) -> None:
        """Initialize video capture with retry logic - tries WebRTC first, falls back to legacy."""
        webrtc_connected = False

        # Try WebRTC first if enabled
        if self.use_webrtc:
            logger.info("Attempting to establish WebRTC peer connection...")
            try:
                self.webrtc_session = CLIWebRTCSession()
                webrtc_connected = await self.webrtc_session.connect()

                if webrtc_connected:
                    logger.info("✅ WebRTC connection established - CLI acting as WebRTC peer")
                    self.stream_ready_event.set()
                    logger.info("Video stream is ready for viewing via WebRTC")
                    # WebRTC session will handle streaming in background
                    return
                else:
                    logger.warning("WebRTC connection failed, falling back to legacy video WebSocket")
                    self.webrtc_session = None

            except Exception as e:
                logger.warning(f"WebRTC initialization error: {e}, falling back to legacy video WebSocket")
                self.webrtc_session = None

        # Fall back to legacy video WebSocket
        logger.info("Using legacy video WebSocket for streaming")
        if await self.websocket_manager.wait_and_connect_with_retry():
            # Signal that the stream is ready once connection is established
            self.stream_ready_event.set()
            logger.info("Video stream is ready for viewing")

            await self.websocket_manager.start_capture_and_stream(self.current_stream_file, self.mp4_queue)
        else:
            logger.error("Failed to establish video stream connection")
            # Don't set the event if connection failed

    async def wait_for_user_response(self, timeout: float) -> Optional[int]:
        """Wait for user response from web UI."""
        logger.info(f"Waiting for user response from web UI (timeout: {timeout}s)...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if we have a response (non-blocking)
                response = self.response_queue.get_nowait()
                logger.info(f"Received user response: {response}")
                return response
            except queue.Empty:
                # No response yet, wait a bit and try again
                await asyncio.sleep(0.1)
                continue

        logger.warning("User response timed out")
        return None

    def get_audio_levels(self) -> dict:
        """Get current audio levels from WebRTC session if active."""
        if self.webrtc_session and self.webrtc_session.connected:
            return self.webrtc_session.get_audio_levels()
        else:
            # Return default values if no WebRTC session
            return {"speaker": 0, "mic": 0}

    async def stop_video_capture_and_stream(self) -> Optional[Path]:
        """Stop video capture and HTTP streaming."""
        # Stop WebRTC session if active
        if self.webrtc_session:
            try:
                await self.webrtc_session.close()
                logger.info("Closed WebRTC session")
            except Exception as e:
                logger.warning(f"Error closing WebRTC session: {e}")
            finally:
                self.webrtc_session = None

        # Stop WebSocket manager
        await self.websocket_manager.stop()

        # Stop HTTP server
        self.http_server.stop()

        # Signal end of stream
        if not self.mp4_queue.full():
            try:
                self.mp4_queue.put_nowait(None)
            except queue.Full:
                pass

        if self.current_stream_file and self.current_stream_file.exists():
            file_size = self.current_stream_file.stat().st_size
            logger.info(f"Video capture saved: {self.current_stream_file}, size: {file_size} bytes")
            return self.current_stream_file
        else:
            logger.info("No video data captured")
            return None
