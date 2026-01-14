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
"""Unit tests for camera_http_server module."""

import queue
from unittest.mock import Mock, patch

import pytest

from th_cli.test_run.camera.camera_http_server import CameraHTTPServer, VideoStreamingHandler


@pytest.mark.unit
class TestCameraHTTPServer:
    """Tests for CameraHTTPServer class."""

    def test_init_default_port(self):
        """Test server initialization with default port."""
        server = CameraHTTPServer()
        assert server.port == 8999
        assert server.server is None
        assert server.server_thread is None

    def test_init_custom_port(self):
        """Test server initialization with custom port."""
        server = CameraHTTPServer(port=9000)
        assert server.port == 9000

    def test_start_server_success(self):
        """Test successful server start."""
        server = CameraHTTPServer(port=0)  # Use port 0 for auto-assignment
        mp4_queue = queue.Queue()
        response_queue = queue.Queue()
        video_handler = Mock()

        with patch("th_cli.test_run.camera.camera_http_server.ThreadingHTTPServer") as mock_server_class:
            mock_server_instance = Mock()
            mock_server_class.return_value = mock_server_instance

            with patch("threading.Thread") as mock_thread:
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance

                server.start(
                    mp4_queue=mp4_queue,
                    response_queue=response_queue,
                    video_handler=video_handler,
                    prompt_options={"PASS": 1, "FAIL": 2},
                    prompt_text="Test prompt",
                    local_ip="192.168.1.100",
                )

                # Verify server creation and configuration
                mock_server_class.assert_called_once_with(("0.0.0.0", 0), VideoStreamingHandler)
                assert mock_server_instance.allow_reuse_address is True
                assert mock_server_instance.mp4_queue == mp4_queue
                assert mock_server_instance.response_queue == response_queue
                assert mock_server_instance.prompt_options == {"PASS": 1, "FAIL": 2}
                assert mock_server_instance.prompt_text == "Test prompt"
                assert mock_server_instance.local_ip == "192.168.1.100"

                # Verify thread creation and start
                mock_thread.assert_called_once()
                mock_thread_instance.start.assert_called_once()

                # Verify server and thread are stored
                assert server.server == mock_server_instance
                assert server.server_thread == mock_thread_instance

    def test_start_server_with_push_av(self):
        """Test server start with Push AV configuration."""
        server = CameraHTTPServer(port=0)
        mp4_queue = queue.Queue()
        response_queue = queue.Queue()

        with patch("th_cli.test_run.camera.camera_http_server.ThreadingHTTPServer") as mock_server_class:
            mock_server_instance = Mock()
            mock_server_class.return_value = mock_server_instance

            with patch("threading.Thread"):
                server.start(
                    mp4_queue=mp4_queue,
                    response_queue=response_queue,
                    video_handler=None,
                    prompt_options={"PASS": 1, "FAIL": 2},
                    prompt_text="Push AV verification",
                    is_push_av_verification=True,
                    push_av_server_url="https://localhost:1234",
                    local_ip="192.168.1.100",
                )

                assert mock_server_instance.is_push_av_verification is True
                assert mock_server_instance.push_av_server_url == "https://localhost:1234"

    def test_stop_server(self):
        """Test server stop."""
        server = CameraHTTPServer()

        # Mock server and thread
        mock_server_instance = Mock()
        mock_thread_instance = Mock()
        server.server = mock_server_instance
        server.server_thread = mock_thread_instance

        server.stop()

        # Verify shutdown called and cleanup
        mock_server_instance.shutdown.assert_called_once()
        assert server.server is None
        assert server.server_thread is None

    def test_stop_server_when_not_running(self):
        """Test stopping server when it's not running."""
        server = CameraHTTPServer()

        # Should not raise an exception
        server.stop()

        assert server.server is None


@pytest.mark.unit
class TestVideoStreamingHandler:
    """Tests for VideoStreamingHandler class."""

    def test_handler_class_exists(self):
        """Test that VideoStreamingHandler class exists and can be imported."""
        # Simple test to verify the class exists
        assert VideoStreamingHandler is not None
        assert hasattr(VideoStreamingHandler, "do_GET")
        assert hasattr(VideoStreamingHandler, "do_POST")
        assert hasattr(VideoStreamingHandler, "do_OPTIONS")

    def test_handler_has_required_methods(self):
        """Test that handler has all required HTTP methods."""
        required_methods = [
            "do_GET",
            "do_POST",
            "do_OPTIONS",
            "stream_live_video",
            "handle_response",
            "handle_streams_api",
            "handle_stream_proxy",
            "handle_simple_proxy",
            "serve_player",
        ]

        for method in required_methods:
            assert hasattr(VideoStreamingHandler, method), f"Missing method: {method}"
