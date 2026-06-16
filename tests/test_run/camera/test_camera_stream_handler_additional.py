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
"""Additional coverage tests for camera_stream_handler.py — covers
start_video_capture_and_stream, wait_for_stream_ready, _initialize_video_capture,
wait_for_user_response, stop_video_capture_and_stream.
"""

import asyncio
import queue
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from th_cli.test_run.camera.camera_stream_handler import CameraStreamHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler(output_dir=None) -> CameraStreamHandler:
    with patch("th_cli.test_run.camera.camera_stream_handler.VideoWebSocketManager"):
        with patch("th_cli.test_run.camera.camera_stream_handler.CameraHTTPServer"):
            if output_dir:
                return CameraStreamHandler(output_dir=str(output_dir))
            with patch.object(Path, "mkdir"):
                return CameraStreamHandler()


# ---------------------------------------------------------------------------
# start_video_capture_and_stream
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStartVideoCaptureAndStream:
    @pytest.mark.asyncio
    async def test_returns_a_path(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        with patch("th_cli.test_run.camera.camera_stream_handler.asyncio.create_task"):
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                result = await h.start_video_capture_and_stream("prompt_1")
        assert isinstance(result, Path)

    @pytest.mark.asyncio
    async def test_path_contains_prompt_id(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        with patch("th_cli.test_run.camera.camera_stream_handler.asyncio.create_task"):
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                result = await h.start_video_capture_and_stream("myprompt42")
        assert "myprompt42" in result.name

    @pytest.mark.asyncio
    async def test_clears_stream_ready_event(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.stream_ready_event.set()  # pre-set it
        with patch("th_cli.test_run.camera.camera_stream_handler.asyncio.create_task"):
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                await h.start_video_capture_and_stream("p")
        assert not h.stream_ready_event.is_set()

    @pytest.mark.asyncio
    async def test_resets_initialization_error(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.initialization_error = "old error"
        with patch("th_cli.test_run.camera.camera_stream_handler.asyncio.create_task"):
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                await h.start_video_capture_and_stream("p")
        assert h.initialization_error is None

    @pytest.mark.asyncio
    async def test_calls_http_server_start(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.prompt_options = {"PASS": 1}
        h.prompt_text = "Check video"
        with patch("th_cli.test_run.camera.camera_stream_handler.asyncio.create_task"):
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                await h.start_video_capture_and_stream("p")
        h.http_server.start.assert_called_once()


# ---------------------------------------------------------------------------
# wait_for_stream_ready
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWaitForStreamReady:
    @pytest.mark.asyncio
    async def test_returns_true_when_event_set_immediately(self):
        h = _make_handler()
        h.stream_ready_event.set()
        result = await h.wait_for_stream_ready(timeout=1.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_timeout(self):
        h = _make_handler()
        with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
            result = await h.wait_for_stream_ready(timeout=0.05)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_event_set_during_wait(self):
        h = _make_handler()

        async def _set_later():
            await asyncio.sleep(0.03)
            h.stream_ready_event.set()

        asyncio.create_task(_set_later())
        result = await h.wait_for_stream_ready(timeout=2.0)
        assert result is True


# ---------------------------------------------------------------------------
# _initialize_video_capture
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInitializeVideoCapture:
    @pytest.mark.asyncio
    async def test_sets_error_when_ffmpeg_not_installed(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.current_stream_file = tmp_path / "vid.bin"

        with patch(
            "th_cli.test_run.camera.camera_stream_handler.FFmpegStreamConverter.check_ffmpeg_installed",
            return_value=(False, "ffmpeg not found"),
        ):
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                await h._initialize_video_capture()

        assert h.initialization_error == "ffmpeg not found"
        assert not h.stream_ready_event.is_set()

    @pytest.mark.asyncio
    async def test_sets_event_when_connect_succeeds(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.current_stream_file = tmp_path / "vid.bin"

        with patch(
            "th_cli.test_run.camera.camera_stream_handler.FFmpegStreamConverter.check_ffmpeg_installed",
            return_value=(True, ""),
        ):
            h.websocket_manager.wait_and_connect_with_retry = AsyncMock(return_value=True)
            h.websocket_manager.start_capture_and_stream = AsyncMock()
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                await h._initialize_video_capture()

        assert h.stream_ready_event.is_set()

    @pytest.mark.asyncio
    async def test_sets_error_when_connect_fails(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.current_stream_file = tmp_path / "vid.bin"

        with patch(
            "th_cli.test_run.camera.camera_stream_handler.FFmpegStreamConverter.check_ffmpeg_installed",
            return_value=(True, ""),
        ):
            h.websocket_manager.wait_and_connect_with_retry = AsyncMock(return_value=False)
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                await h._initialize_video_capture()

        assert h.initialization_error is not None
        assert not h.stream_ready_event.is_set()

    @pytest.mark.asyncio
    async def test_handles_unexpected_exception(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.current_stream_file = tmp_path / "vid.bin"

        with patch(
            "th_cli.test_run.camera.camera_stream_handler.FFmpegStreamConverter.check_ffmpeg_installed",
            side_effect=RuntimeError("unexpected"),
        ):
            with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
                await h._initialize_video_capture()  # must not raise

        assert h.initialization_error is not None


# ---------------------------------------------------------------------------
# wait_for_user_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWaitForUserResponseStream:
    @pytest.mark.asyncio
    async def test_returns_queued_response_immediately(self):
        h = _make_handler()
        h.response_queue.put_nowait(1)
        result = await h.wait_for_user_response(timeout=1.0)
        assert result == 1

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self):
        h = _make_handler()
        with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
            result = await h.wait_for_user_response(timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_response_enqueued_during_wait(self):
        h = _make_handler()

        async def _enqueue_later():
            await asyncio.sleep(0.05)
            h.response_queue.put_nowait(42)

        asyncio.create_task(_enqueue_later())
        with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
            result = await h.wait_for_user_response(timeout=2.0)
        assert result == 42


# ---------------------------------------------------------------------------
# stop_video_capture_and_stream
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStopVideoCaptureAndStream:
    @pytest.mark.asyncio
    async def test_stops_websocket_and_http_server(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        h.websocket_manager.stop = AsyncMock()

        with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
            await h.stop_video_capture_and_stream()

        h.websocket_manager.stop.assert_called_once()
        h.http_server.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_stream_file(self):
        h = _make_handler()
        h.current_stream_file = None
        h.websocket_manager.stop = AsyncMock()
        with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
            result = await h.stop_video_capture_and_stream()
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_path_when_stream_file_exists(self, tmp_path):
        h = _make_handler(output_dir=tmp_path)
        stream_file = tmp_path / "vid.bin"
        stream_file.write_bytes(b"data")
        h.current_stream_file = stream_file
        h.websocket_manager.stop = AsyncMock()
        with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
            result = await h.stop_video_capture_and_stream()
        assert result == stream_file

    @pytest.mark.asyncio
    async def test_puts_none_sentinel_in_mp4_queue(self):
        h = _make_handler()
        h.websocket_manager.stop = AsyncMock()
        with patch("th_cli.test_run.camera.camera_stream_handler.logger"):
            await h.stop_video_capture_and_stream()
        # Queue should have None sentinel
        assert h.mp4_queue.get_nowait() is None
