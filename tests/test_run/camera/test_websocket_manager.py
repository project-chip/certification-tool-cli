#
# Copyright (c) 2025-2026 Project CHIP Authors
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
"""Unit tests for th_cli/test_run/camera/websocket_manager.py."""

import asyncio
import queue
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from th_cli.test_run.camera.websocket_manager import VideoWebSocketManager


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoWebSocketManagerInit:
    def test_video_websocket_initially_none(self):
        mgr = VideoWebSocketManager()
        assert mgr.video_websocket is None

    def test_streaming_active_initially_false(self):
        mgr = VideoWebSocketManager()
        assert mgr.streaming_active is False

    def test_ffmpeg_converter_initially_none(self):
        mgr = VideoWebSocketManager()
        assert mgr.ffmpeg_converter is None


# ---------------------------------------------------------------------------
# connect()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoWebSocketManagerConnect:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        mgr = VideoWebSocketManager()
        mock_ws = AsyncMock()
        # ping() returns a future; wait_for on it should resolve without blocking
        pong_future = asyncio.get_event_loop().create_future()
        pong_future.set_result(None)
        mock_ws.ping = AsyncMock(return_value=pong_future)

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            with patch(
                "th_cli.test_run.camera.websocket_manager.websocket_connect",
                new_callable=AsyncMock,
                return_value=mock_ws,
            ):
                result = await mgr.connect()

        assert result is True
        assert mgr.video_websocket is mock_ws

    @pytest.mark.asyncio
    async def test_returns_false_when_connect_raises(self):
        mgr = VideoWebSocketManager()
        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            with patch(
                "th_cli.test_run.camera.websocket_manager.websocket_connect",
                side_effect=ConnectionRefusedError("refused"),
            ):
                result = await mgr.connect()

        assert result is False
        assert mgr.video_websocket is None

    @pytest.mark.asyncio
    async def test_returns_true_even_when_ping_fails(self):
        """Ping failure is non-fatal — connect should still return True."""
        mgr = VideoWebSocketManager()
        mock_ws = AsyncMock()
        mock_ws.ping = AsyncMock(side_effect=Exception("ping timeout"))

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            with patch(
                "th_cli.test_run.camera.websocket_manager.websocket_connect",
                new_callable=AsyncMock,
                return_value=mock_ws,
            ):
                result = await mgr.connect()

        assert result is True


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoWebSocketManagerReset:
    def test_sets_streaming_active_false(self):
        mgr = VideoWebSocketManager()
        mgr.streaming_active = True
        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            mgr.reset()
        assert mgr.streaming_active is False

    def test_stops_ffmpeg_converter_if_present(self):
        mgr = VideoWebSocketManager()
        mock_converter = MagicMock()
        mgr.ffmpeg_converter = mock_converter

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            mgr.reset()

        mock_converter.stop.assert_called_once()
        assert mgr.ffmpeg_converter is None

    def test_ffmpeg_converter_none_when_not_present(self):
        mgr = VideoWebSocketManager()
        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            mgr.reset()
        assert mgr.ffmpeg_converter is None

    def test_handles_converter_stop_exception(self):
        mgr = VideoWebSocketManager()
        mock_converter = MagicMock()
        mock_converter.stop.side_effect = RuntimeError("already stopped")
        mgr.ffmpeg_converter = mock_converter

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            mgr.reset()  # must not raise

        assert mgr.ffmpeg_converter is None


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoWebSocketManagerStop:
    @pytest.mark.asyncio
    async def test_sets_streaming_active_false(self):
        mgr = VideoWebSocketManager()
        mgr.streaming_active = True
        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            await mgr.stop()
        assert mgr.streaming_active is False

    @pytest.mark.asyncio
    async def test_stops_ffmpeg_converter_if_present(self):
        mgr = VideoWebSocketManager()
        mock_converter = MagicMock()
        mgr.ffmpeg_converter = mock_converter

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            await mgr.stop()

        mock_converter.stop.assert_called_once()
        assert mgr.ffmpeg_converter is None

    @pytest.mark.asyncio
    async def test_closes_websocket_if_present(self):
        mgr = VideoWebSocketManager()
        mock_ws = AsyncMock()
        mgr.video_websocket = mock_ws

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            await mgr.stop()

        mock_ws.close.assert_called_once()
        assert mgr.video_websocket is None

    @pytest.mark.asyncio
    async def test_noop_when_all_fields_none(self):
        mgr = VideoWebSocketManager()
        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            await mgr.stop()  # must not raise
        assert mgr.streaming_active is False

    @pytest.mark.asyncio
    async def test_handles_close_exception_gracefully(self):
        mgr = VideoWebSocketManager()
        mock_ws = AsyncMock()
        mock_ws.close.side_effect = Exception("already closed")
        mgr.video_websocket = mock_ws

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            await mgr.stop()  # must not raise

        assert mgr.video_websocket is None


# ---------------------------------------------------------------------------
# start_capture_and_stream() — no-op when not connected
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStartCaptureAndStream:
    @pytest.mark.asyncio
    async def test_returns_immediately_when_not_connected(self):
        mgr = VideoWebSocketManager()
        # video_websocket is None — should log error and return immediately
        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            await mgr.start_capture_and_stream(stream_file=None, mp4_queue=None)
        assert mgr.streaming_active is False


# ---------------------------------------------------------------------------
# wait_and_connect_with_retry()
#
# NOTE: In the source, the retry loop only increments `attempt` inside the
# `except` block — so a `connect()` that consistently returns False (without
# raising) causes an infinite loop.  We therefore test:
#   1. connect() succeeds → returns True immediately
#   2. connect() raises each time → retries up to max_attempts, returns False
#   3. Pre-existing websocket is closed before first attempt
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWaitAndConnectWithRetry:
    @pytest.mark.asyncio
    async def test_returns_true_on_first_success(self):
        mgr = VideoWebSocketManager()

        with patch.object(mgr, "connect", new_callable=AsyncMock, return_value=True):
            with patch("th_cli.test_run.camera.websocket_manager.logger"):
                result = await mgr.wait_and_connect_with_retry(max_attempts=3)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_after_all_attempts_raise(self):
        """Retry loop increments attempt only on exception; use side_effect to raise."""
        mgr = VideoWebSocketManager()

        with patch.object(
            mgr, "connect", new_callable=AsyncMock, side_effect=ConnectionRefusedError("refused")
        ):
            with patch(
                "th_cli.test_run.camera.websocket_manager.asyncio.sleep",
                new_callable=AsyncMock,
            ):
                with patch("th_cli.test_run.camera.websocket_manager.logger"):
                    result = await mgr.wait_and_connect_with_retry(max_attempts=2)

        assert result is False

    @pytest.mark.asyncio
    async def test_closes_existing_websocket_before_connecting(self):
        mgr = VideoWebSocketManager()
        mock_ws = AsyncMock()
        mgr.video_websocket = mock_ws

        with patch.object(mgr, "connect", new_callable=AsyncMock, return_value=True):
            with patch("th_cli.test_run.camera.websocket_manager.logger"):
                await mgr.wait_and_connect_with_retry(max_attempts=1)

        mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_existing_websocket_close_error(self):
        mgr = VideoWebSocketManager()
        mock_ws = AsyncMock()
        mock_ws.close.side_effect = Exception("already closed")
        mgr.video_websocket = mock_ws

        with patch.object(mgr, "connect", new_callable=AsyncMock, return_value=True):
            with patch("th_cli.test_run.camera.websocket_manager.logger"):
                result = await mgr.wait_and_connect_with_retry(max_attempts=1)

        assert result is True


# ---------------------------------------------------------------------------
# _transfer_converted_data()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTransferConvertedData:
    def test_puts_converted_data_into_queue(self):
        mgr = VideoWebSocketManager()
        mgr.streaming_active = True

        mock_converter = MagicMock()
        call_count = [0]

        def get_converted_data(timeout=1.0):
            call_count[0] += 1
            if call_count[0] == 1:
                return b"mp4chunk"
            mgr.streaming_active = False  # stop after first chunk
            return None

        mock_converter.get_converted_data.side_effect = get_converted_data
        mgr.ffmpeg_converter = mock_converter

        mp4_queue = queue.Queue()

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            mgr._transfer_converted_data(mp4_queue)

        assert not mp4_queue.empty()
        assert mp4_queue.get_nowait() == b"mp4chunk"

    def test_handles_full_queue_without_exception(self):
        mgr = VideoWebSocketManager()
        mgr.streaming_active = True

        mock_converter = MagicMock()
        call_count = [0]

        def get_converted_data(timeout=1.0):
            call_count[0] += 1
            if call_count[0] == 1:
                return b"data"
            mgr.streaming_active = False
            return None

        mock_converter.get_converted_data.side_effect = get_converted_data
        mgr.ffmpeg_converter = mock_converter

        # Pre-fill queue to capacity so the put_nowait raises queue.Full
        mp4_queue_full = queue.Queue(maxsize=1)
        mp4_queue_full.put_nowait(b"already_full")

        with patch("th_cli.test_run.camera.websocket_manager.logger"):
            mgr._transfer_converted_data(mp4_queue_full)  # must not raise
