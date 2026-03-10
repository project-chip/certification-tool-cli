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
"""Unit tests for CameraStreamHandler."""

import asyncio
import queue
from pathlib import Path
from unittest.mock import patch

import pytest

from th_cli.test_run.camera.camera_stream_handler import CameraStreamHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler(output_dir=None) -> CameraStreamHandler:
    """Construct a CameraStreamHandler with mocked sub-components."""
    with patch("th_cli.test_run.camera.camera_stream_handler.VideoWebSocketManager"):
        with patch("th_cli.test_run.camera.camera_stream_handler.CameraHTTPServer"):
            if output_dir:
                return CameraStreamHandler(output_dir=str(output_dir))
            with patch.object(Path, "mkdir"):
                return CameraStreamHandler()


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCameraStreamHandlerInit:
    def test_response_queue_is_queue(self):
        h = _make_handler()
        assert isinstance(h.response_queue, queue.Queue)

    def test_mp4_queue_is_queue(self):
        h = _make_handler()
        assert isinstance(h.mp4_queue, queue.Queue)

    def test_prompt_options_initially_empty(self):
        h = _make_handler()
        assert h.prompt_options == {}

    def test_prompt_text_initially_empty_string(self):
        h = _make_handler()
        assert h.prompt_text == ""

    def test_initialization_error_initially_none(self):
        h = _make_handler()
        assert h.initialization_error is None


# ---------------------------------------------------------------------------
# set_prompt_data
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSetPromptData:
    def test_stores_prompt_text_and_options(self):
        h = _make_handler()
        h.set_prompt_data("Is the video clear?", {"PASS": 1, "FAIL": 2})
        assert h.prompt_text == "Is the video clear?"
        assert h.prompt_options == {"PASS": 1, "FAIL": 2}

    def test_overwrites_previous_values(self):
        h = _make_handler()
        h.set_prompt_data("First", {"A": 1})
        h.set_prompt_data("Second", {"B": 2})
        assert h.prompt_text == "Second"
        assert h.prompt_options == {"B": 2}

    def test_empty_options_stored(self):
        h = _make_handler()
        h.set_prompt_data("No options", {})
        assert h.prompt_options == {}


# ---------------------------------------------------------------------------
# wait_for_user_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWaitForUserResponse:
    @pytest.mark.asyncio
    async def test_returns_pre_queued_response_immediately(self):
        h = _make_handler()
        h.response_queue.put_nowait(1)
        result = await h.wait_for_user_response(timeout=1.0)
        assert result == 1

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self):
        h = _make_handler()
        result = await h.wait_for_user_response(timeout=0.15)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_response_enqueued_during_wait(self):
        h = _make_handler()

        async def enqueue_later():
            await asyncio.sleep(0.05)
            h.response_queue.put_nowait(2)

        results = await asyncio.gather(enqueue_later(), h.wait_for_user_response(timeout=1.0))
        assert results[1] == 2

    @pytest.mark.asyncio
    async def test_returns_first_response_when_multiple_queued(self):
        h = _make_handler()
        h.response_queue.put_nowait(10)
        h.response_queue.put_nowait(20)
        result = await h.wait_for_user_response(timeout=1.0)
        assert result == 10
