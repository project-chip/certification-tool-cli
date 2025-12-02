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
from typing import Optional

import numpy as np
from aiortc import RTCConfiguration, RTCIceCandidate, RTCIceServer, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamTrack
from av import AudioFrame, VideoFrame
from loguru import logger
from websockets.client import WebSocketClientProtocol, connect as websocket_connect

from th_cli.config import config


class CLIWebRTCSession:
    """Handles WebRTC peer connection for CLI to get audio and video from device."""

    def __init__(self):
        self.peer_connection: Optional[RTCPeerConnection] = None
        self.signaling_websocket: Optional[WebSocketClientProtocol] = None
        self.audio_track: Optional[MediaStreamTrack] = None
        self.video_track: Optional[MediaStreamTrack] = None

        # Audio level state
        self.remote_audio_level = 0  # Speaker level (from device)
        self.local_audio_level = 0   # Mic level (to device)

        # Video data queue for HTTP streaming
        self.video_queue = queue.Queue(maxsize=100)

        # Connection state
        self.connected = False
        self.connection_state = "unknown"

        # Session ID for signaling
        self.session_id = "cli-session"

        # ICE candidates buffer
        self.ice_candidates = []

    async def connect(self) -> bool:
        """Connect to device via WebRTC using backend signaling."""
        try:
            # Connect to backend WebRTC signaling WebSocket as PEER
            # The test backend connects as CONTROLLER, and backend relays messages between them
            webrtc_ws_url = f"ws://{config.hostname}/api/v1/ws/webrtc/peer"
            logger.info(f"Connecting to WebRTC signaling: {webrtc_ws_url}")
            print(f"DEBUG: Connecting to WebRTC signaling: {webrtc_ws_url}", flush=True)

            self.signaling_websocket = await websocket_connect(webrtc_ws_url, ping_timeout=None)
            logger.info("WebRTC signaling WebSocket connected")
            print("DEBUG: WebRTC signaling WebSocket connected", flush=True)

            # Create peer connection with STUN servers
            configuration = RTCConfiguration(
                iceServers=[
                    RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                    RTCIceServer(urls=["stun:stun1.l.google.com:19302"]),
                ]
            )

            self.peer_connection = RTCPeerConnection(configuration)
            logger.info("Created RTCPeerConnection")
            print("DEBUG: Created RTCPeerConnection", flush=True)

            # Add transceivers for audio and video (receive only)
            self.peer_connection.addTransceiver("audio", direction="recvonly")
            self.peer_connection.addTransceiver("video", direction="recvonly")
            logger.info("Added audio and video transceivers (recvonly)")
            print("DEBUG: Added audio and video transceivers (recvonly)", flush=True)

            # Set up event handlers
            self._setup_event_handlers()

            # Start signaling message handler task
            asyncio.create_task(self._handle_signaling_messages())

            # As a PEER, we wait for the CONTROLLER to send an offer
            # We don't create an offer ourselves
            logger.info("WebRTC peer ready - waiting for controller to send offer...")
            print("DEBUG: WebRTC peer ready - waiting for controller offer", flush=True)

            # Return True immediately - we're connected to signaling and ready
            # The actual WebRTC connection will happen when controller sends offer
            return True

        except Exception as e:
            logger.error(f"Failed to establish WebRTC signaling connection: {e}")
            print(f"DEBUG: Failed to establish WebRTC signaling connection: {e}", flush=True)
            return False

    def _setup_event_handlers(self):
        """Set up WebRTC event handlers."""

        @self.peer_connection.on("track")
        async def on_track(track: MediaStreamTrack):
            """Handle incoming media tracks."""
            logger.info(f"Received {track.kind} track")

            if track.kind == "audio":
                self.audio_track = track
                # Start audio analysis task
                asyncio.create_task(self._analyze_audio_track(track))

            elif track.kind == "video":
                self.video_track = track
                # Start video processing task
                asyncio.create_task(self._process_video_track(track))

        @self.peer_connection.on("connectionstatechange")
        async def on_connection_state_change():
            """Handle connection state changes."""
            state = self.peer_connection.connectionState
            self.connection_state = state
            logger.info(f"Connection state changed to: {state}")

            if state == "connected":
                self.connected = True
            elif state in ("failed", "closed"):
                self.connected = False

        @self.peer_connection.on("icecandidate")
        async def on_ice_candidate(candidate):
            """Handle ICE candidates."""
            if candidate:
                logger.debug(f"Got ICE candidate: {candidate}")
                # Send ICE candidate to peer via signaling
                await self._send_ice_candidate(candidate)

    async def _create_and_send_offer(self):
        """Create WebRTC offer and send to device via signaling."""
        # Create offer
        offer = await self.peer_connection.createOffer()
        await self.peer_connection.setLocalDescription(offer)

        logger.info("Created WebRTC offer")
        print("DEBUG: Created WebRTC offer", flush=True)

        # Send offer to device via backend signaling
        # Use camelCase "sessionId" to match backend format
        message = {
            "type": "CREATE_OFFER",
            "sessionId": self.session_id,  # Use camelCase!
            "data": self.peer_connection.localDescription.sdp,
            "error": None,
        }

        await self.signaling_websocket.send(json.dumps(message))
        logger.info("Sent offer to device via signaling")
        print(f"DEBUG: Sent offer message: {json.dumps(message, indent=2)[:200]}...", flush=True)

    async def _handle_signaling_messages(self):
        """Handle incoming signaling messages from backend."""
        logger.info("Starting signaling message handler")
        print("DEBUG: Starting signaling message handler", flush=True)

        try:
            while self.signaling_websocket:
                try:
                    message_str = await self.signaling_websocket.recv()
                    message = json.loads(message_str)

                    message_type = message.get("type")
                    logger.debug(f"Received signaling message: {message_type}")
                    print(f"DEBUG: Received signaling message: {message_type}", flush=True)
                    print(f"DEBUG: Full message: {json.dumps(message, indent=2)}", flush=True)

                    if message_type == "CREATE_PEER_CONNECTION":
                        # Controller is requesting peer connection initialization
                        # We already initialized in connect(), so just acknowledge
                        # IMPORTANT: Use "sessionId" (camelCase) not "session_id" (snake_case)
                        session_id = message.get("sessionId", message.get("session_id", self.session_id))

                        # Update our session ID to match the controller's session
                        self.session_id = session_id

                        logger.info(f"Acknowledging peer connection for session: {session_id}")
                        print(f"DEBUG: Acknowledging CREATE_PEER_CONNECTION for session: {session_id}", flush=True)

                        # Send acknowledgement response - match the exact format
                        # Must use camelCase "sessionId" to match incoming format
                        ack_message = {
                            "type": message.get("type"),
                            "sessionId": session_id,  # Use camelCase!
                            "data": None,
                            "error": None,
                        }

                        # Include event_id if present in original message (for correlation)
                        if "event_id" in message:
                            ack_message["event_id"] = message["event_id"]
                        if "message_id" in message:
                            ack_message["message_id"] = message["message_id"]

                        await self.signaling_websocket.send(json.dumps(ack_message))
                        logger.info(f"Sent peer connection acknowledgement: {ack_message}")
                        print(f"DEBUG: Sent acknowledgement: {json.dumps(ack_message, indent=2)}", flush=True)

                    elif message_type == "CREATE_OFFER":
                        # Controller is requesting us to create an offer
                        # This is the controller asking peer to create offer
                        session_id = message.get("session_id", self.session_id)
                        media_direction = message.get("data")  # e.g., "recvonly"
                        logger.info(f"Received CREATE_OFFER request with direction: {media_direction}")
                        print(f"DEBUG: Creating offer with direction: {media_direction}", flush=True)
                        await self._create_and_send_offer()

                    elif message_type == "SET_REMOTE_OFFER":
                        # Received offer from controller - create answer
                        offer_sdp = message.get("data")
                        await self.set_remote_offer_and_create_answer(offer_sdp)

                    elif message_type == "SET_REMOTE_ANSWER":
                        # Received answer from device
                        answer_sdp = message.get("data")
                        await self.set_remote_answer(answer_sdp)

                    elif message_type == "SET_REMOTE_ICE_CANDIDATES":
                        # Received ICE candidates from device
                        candidates = message.get("data", [])
                        for candidate_data in candidates:
                            await self.add_ice_candidate(candidate_data)

                    elif message_type == "PEER_CONNECTION_STATE":
                        state = message.get("data")
                        logger.info(f"Peer connection state from backend: {state}")
                        print(f"DEBUG: Peer connection state: {state}", flush=True)

                    elif message_type == "CLOSE_PEER_CONNECTION":
                        # Backend is asking us to close the peer connection
                        # This can happen if controller is not ready yet
                        error_msg = message.get("error", "Unknown error")
                        logger.warning(f"Backend requested peer connection close: {error_msg}")
                        print(f"DEBUG: Backend requested close: {error_msg}. Keeping signaling alive...", flush=True)
                        # Don't break - keep signaling connection alive
                        # The test will create controller later and we'll be ready
                        continue

                except Exception as e:
                    logger.error(f"Error processing signaling message: {e}")
                    print(f"DEBUG: Error processing signaling message: {e}", flush=True)
                    break

        except Exception as e:
            logger.error(f"Signaling message handler error: {e}")
            print(f"DEBUG: Signaling message handler error: {e}", flush=True)

        logger.info("Signaling message handler ended")
        print("DEBUG: Signaling message handler ended", flush=True)

    async def _send_ice_candidate(self, candidate):
        """Send ICE candidate to peer via signaling."""
        # Use camelCase "sessionId" to match backend format
        message = {
            "type": "LOCAL_ICE_CANDIDATES",
            "sessionId": self.session_id,  # Use camelCase!
            "data": {
                "candidate": candidate.candidate,
                "sdpMLineIndex": candidate.sdpMLineIndex,
                "sdpMid": candidate.sdpMid,
            },
        }

        await self.signaling_websocket.send(json.dumps(message))
        logger.debug("Sent ICE candidate to device")

    async def set_remote_offer_and_create_answer(self, offer_sdp: str):
        """Set remote offer from controller and create answer."""
        try:
            # Set the remote offer
            offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
            await self.peer_connection.setRemoteDescription(offer)
            logger.info("Set remote offer from controller")
            print("DEBUG: Set remote offer from controller", flush=True)

            # Create answer
            answer = await self.peer_connection.createAnswer()
            await self.peer_connection.setLocalDescription(answer)
            logger.info("Created answer to controller offer")
            print("DEBUG: Created answer", flush=True)

            # Send answer to controller via signaling
            # Use camelCase "sessionId" to match backend format
            message = {
                "type": "CREATE_ANSWER",
                "sessionId": self.session_id,  # Use camelCase!
                "data": self.peer_connection.localDescription.sdp,
                "error": None,
            }

            await self.signaling_websocket.send(json.dumps(message))
            logger.info("Sent answer to controller")
            print(f"DEBUG: Sent answer message: {json.dumps(message, indent=2)[:200]}...", flush=True)

        except Exception as e:
            logger.error(f"Error handling offer and creating answer: {e}")
            print(f"DEBUG: Error handling offer: {e}", flush=True)

    async def set_remote_answer(self, answer_sdp: str):
        """Set remote answer from device."""
        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await self.peer_connection.setRemoteDescription(answer)
        logger.info("Set remote answer from device")

    async def add_ice_candidate(self, candidate_data: dict):
        """Add ICE candidate from device."""
        candidate = RTCIceCandidate(
            candidate=candidate_data["candidate"],
            sdpMLineIndex=candidate_data.get("sdpMLineIndex", 0),
            sdpMid=candidate_data.get("sdpMid", "0"),
        )
        await self.peer_connection.addIceCandidate(candidate)
        logger.debug("Added ICE candidate from device")

    async def _wait_for_connection(self, timeout: float = 30.0):
        """Wait for WebRTC connection to be established."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if self.connection_state == "connected":
                logger.info("WebRTC connection established")
                return True
            elif self.connection_state in ("failed", "closed"):
                logger.error(f"WebRTC connection failed with state: {self.connection_state}")
                return False

            await asyncio.sleep(0.1)

        logger.error("WebRTC connection timeout")
        return False

    async def _analyze_audio_track(self, track: MediaStreamTrack):
        """Analyze audio track to extract real-time audio levels."""
        logger.info("Starting audio analysis")

        try:
            async for frame in track:
                if isinstance(frame, AudioFrame):
                    # Convert audio frame to numpy array
                    try:
                        audio_data = frame.to_ndarray()

                        # Calculate RMS (Root Mean Square) for audio level
                        # RMS gives us the power/loudness of the audio signal
                        rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))

                        # Convert to percentage (0-100)
                        # Typical audio values are -1.0 to 1.0, so RMS will be 0.0 to ~0.7
                        # We scale by a factor to get reasonable percentage values
                        level = min(100, int(rms * 200))

                        # Update remote audio level (speaker - from device)
                        self.remote_audio_level = level

                        logger.debug(f"Audio level: {level}%")

                    except Exception as e:
                        logger.error(f"Error processing audio frame: {e}")

        except Exception as e:
            logger.error(f"Audio track ended or error: {e}")

    async def _process_video_track(self, track: MediaStreamTrack):
        """Process video track - extract frames for HTTP streaming."""
        logger.info("Starting video processing")

        try:
            async for frame in track:
                if isinstance(frame, VideoFrame):
                    try:
                        # Convert video frame to bytes for streaming
                        # aiortc provides frames as av.VideoFrame
                        # We can encode them to JPEG or H.264 for streaming

                        # For now, we'll just log that we're receiving video
                        # The actual streaming can use the existing FFmpeg pipeline
                        logger.debug(f"Received video frame: {frame.width}x{frame.height}")

                        # Put frame in queue for HTTP streaming (if needed)
                        # This would replace the UDP video stream

                    except queue.Full:
                        # Drop frame if queue is full
                        logger.debug("Video queue full, dropping frame")

                    except Exception as e:
                        logger.error(f"Error processing video frame: {e}")

        except Exception as e:
            logger.error(f"Video track ended or error: {e}")

    def get_audio_levels(self) -> dict:
        """Get current audio levels."""
        return {
            "speaker": self.remote_audio_level,  # Audio from device (remote)
            "mic": self.local_audio_level,       # Audio to device (local, always 0 for recvonly)
        }

    async def close(self):
        """Close WebRTC connection."""
        if self.peer_connection:
            await self.peer_connection.close()
            logger.info("Closed WebRTC connection")

        self.connected = False
        self.connection_state = "closed"
