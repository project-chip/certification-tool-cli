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
"""Unit tests for prompt_manager module."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from th_cli.shared_constants import MessageTypeEnum
from th_cli.test_run import prompt_manager
from th_cli.test_run.socket_schemas import (
    ImageVerificationPromptRequest,
    MessagePromptRequest,
    OptionsSelectPromptRequest,
    PushAVStreamVerificationRequest,
    StreamVerificationPromptRequest,
    TextInputPromptRequest,
    UserResponseStatusEnum,
)


@pytest.mark.unit
class TestGetLocalIp:
    """Tests for _get_local_ip function."""

    def test_get_local_ip_success(self):
        """Test successful local IP retrieval."""
        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.getsockname.return_value = ("192.168.1.100", 12345)
            mock_socket.return_value.__enter__.return_value = mock_sock

            result = prompt_manager._get_local_ip()

            assert result == "192.168.1.100"
            mock_sock.connect.assert_called_once_with(("8.8.8.8", 80))

    def test_get_local_ip_fallback_on_error(self):
        """Test fallback to localhost on connection error."""
        with patch("socket.socket") as mock_socket:
            mock_socket.return_value.__enter__.side_effect = Exception("Network error")

            result = prompt_manager._get_local_ip()

            assert result == "localhost"


@pytest.mark.unit
class TestGetVideoHandler:
    """Tests for _get_video_handler function."""

    def test_get_video_handler_creates_instance(self):
        """Test that video handler instance is created on first call."""
        # Reset global instance
        prompt_manager._video_handler_instance = None

        with patch("th_cli.test_run.camera.CameraStreamHandler") as mock_handler:
            mock_instance = MagicMock()
            mock_handler.return_value = mock_instance

            result = prompt_manager._get_video_handler()

            assert result == mock_instance
            mock_handler.assert_called_once()

    def test_get_video_handler_reuses_instance(self):
        """Test that video handler instance is reused on subsequent calls."""
        mock_instance = MagicMock()
        prompt_manager._video_handler_instance = mock_instance

        with patch("th_cli.test_run.camera.CameraStreamHandler") as mock_handler:
            result = prompt_manager._get_video_handler()

            assert result == mock_instance
            mock_handler.assert_not_called()


@pytest.mark.unit
class TestCleanupVideoHandler:
    """Tests for _cleanup_video_handler function."""

    @pytest.mark.asyncio
    async def test_cleanup_video_handler_success(self):
        """Test successful cleanup of video handler."""
        mock_instance = MagicMock()
        mock_instance.stop_video_capture_and_stream = AsyncMock()
        prompt_manager._video_handler_instance = mock_instance

        await prompt_manager._cleanup_video_handler()

        mock_instance.stop_video_capture_and_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_video_handler_no_instance(self):
        """Test cleanup when no instance exists."""
        prompt_manager._video_handler_instance = None

        # Should not raise an exception
        await prompt_manager._cleanup_video_handler()

    @pytest.mark.asyncio
    async def test_cleanup_video_handler_error_ignored(self):
        """Test that cleanup errors are ignored."""
        mock_instance = MagicMock()
        mock_instance.stop_video_capture_and_stream = AsyncMock(side_effect=Exception("Cleanup error"))
        prompt_manager._video_handler_instance = mock_instance

        # Should not raise an exception
        await prompt_manager._cleanup_video_handler()


@pytest.mark.unit
class TestHandlePrompt:
    """Tests for handle_prompt function."""

    @pytest.mark.asyncio
    async def test_handle_prompt_image_verification(self):
        """Test routing to image verification handler."""
        mock_socket = AsyncMock()
        mock_request = ImageVerificationPromptRequest(
            message_id=1,
            prompt="Verify image",
            timeout=30,
            options={"PASS": 1, "FAIL": 2},
            image_hex_str="ffd8ffe0",
        )

        with patch("th_cli.test_run.prompt_manager.__handle_image_verification_prompt") as mock_handler:
            mock_handler.return_value = asyncio.Future()
            mock_handler.return_value.set_result(None)

            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=mock_request,
                message_type=MessageTypeEnum.IMAGE_VERIFICATION_REQUEST,
            )

            mock_handler.assert_called_once_with(socket=mock_socket, prompt=mock_request)

    @pytest.mark.asyncio
    async def test_handle_prompt_stream_verification(self):
        """Test routing to stream verification handler."""
        mock_socket = AsyncMock()
        mock_request = StreamVerificationPromptRequest(
            message_id=2,
            prompt="Verify stream",
            timeout=120,
            options={"PASS": 1, "FAIL": 2},
        )

        with patch("th_cli.test_run.prompt_manager.__handle_stream_verification_prompt") as mock_handler:
            mock_handler.return_value = asyncio.Future()
            mock_handler.return_value.set_result(None)

            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=mock_request,
                message_type=MessageTypeEnum.STREAM_VERIFICATION_REQUEST,
            )

            mock_handler.assert_called_once_with(socket=mock_socket, prompt=mock_request)

    @pytest.mark.asyncio
    async def test_handle_prompt_push_av_stream(self):
        """Test routing to Push AV stream handler."""
        mock_socket = AsyncMock()
        mock_request = PushAVStreamVerificationRequest(
            message_id=3,
            prompt="Verify Push AV stream",
            timeout=120,
            options={"PASS": 1, "FAIL": 2},
        )

        with patch("th_cli.test_run.prompt_manager.__handle_push_av_stream_prompt") as mock_handler:
            mock_handler.return_value = asyncio.Future()
            mock_handler.return_value.set_result(None)

            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=mock_request,
                message_type=MessageTypeEnum.PUSH_AV_STREAM_VERIFICATION_REQUEST,
            )

            mock_handler.assert_called_once_with(socket=mock_socket, prompt=mock_request)

    @pytest.mark.asyncio
    async def test_handle_prompt_message_request(self):
        """Test routing to message handler."""
        mock_socket = AsyncMock()
        mock_request = MessagePromptRequest(
            message_id=4,
            prompt="Acknowledge this message",
            timeout=30,
        )

        with patch("th_cli.test_run.prompt_manager.__handle_message_prompt") as mock_handler:
            mock_handler.return_value = asyncio.Future()
            mock_handler.return_value.set_result(None)

            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=mock_request,
                message_type=MessageTypeEnum.MESSAGE_REQUEST,
            )

            mock_handler.assert_called_once_with(socket=mock_socket, prompt=mock_request)

    @pytest.mark.asyncio
    async def test_handle_prompt_options_select(self):
        """Test routing to options prompt handler."""
        mock_socket = AsyncMock()
        mock_request = OptionsSelectPromptRequest(
            message_id=5,
            prompt="Select an option",
            timeout=30,
            options={"Option 1": 1, "Option 2": 2},
        )

        with patch("th_cli.test_run.prompt_manager.__handle_options_prompt") as mock_handler:
            mock_handler.return_value = asyncio.Future()
            mock_handler.return_value.set_result(None)

            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=mock_request,
            )

            mock_handler.assert_called_once_with(socket=mock_socket, prompt=mock_request)

    @pytest.mark.asyncio
    async def test_handle_prompt_text_input(self):
        """Test routing to text input handler."""
        mock_socket = AsyncMock()
        mock_request = TextInputPromptRequest(
            message_id=6,
            prompt="Enter text",
            timeout=30,
        )

        with patch("th_cli.test_run.prompt_manager.__handle_text_prompt") as mock_handler:
            mock_handler.return_value = asyncio.Future()
            mock_handler.return_value.set_result(None)

            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=mock_request,
            )

            mock_handler.assert_called_once_with(socket=mock_socket, prompt=mock_request)


@pytest.mark.unit
class TestSendPromptResponse:
    """Tests for _send_prompt_response function."""

    @pytest.mark.asyncio
    async def test_send_prompt_response_success(self):
        """Test successful prompt response sending."""
        mock_socket = AsyncMock()
        mock_prompt = Mock()
        mock_prompt.message_id = 123

        await prompt_manager._send_prompt_response(
            socket=mock_socket,
            prompt=mock_prompt,
            response="test response",
            status_code=UserResponseStatusEnum.OKAY,
        )

        mock_socket.send.assert_called_once()
        call_args = mock_socket.send.call_args[0][0]

        payload = json.loads(call_args)
        assert payload["type"] == "prompt_response"
        assert payload["payload"]["response"] == "test response"
        assert payload["payload"]["status_code"] == UserResponseStatusEnum.OKAY
        assert payload["payload"]["message_id"] == 123

    @pytest.mark.asyncio
    async def test_send_prompt_response_cancelled_status(self):
        """Test prompt response with CANCELLED status."""
        mock_socket = AsyncMock()
        mock_prompt = Mock()
        mock_prompt.message_id = 456

        await prompt_manager._send_prompt_response(
            socket=mock_socket,
            prompt=mock_prompt,
            response="Stream failed",
            status_code=UserResponseStatusEnum.CANCELLED,
        )

        mock_socket.send.assert_called_once()
        call_args = mock_socket.send.call_args[0][0]

        payload = json.loads(call_args)
        assert payload["payload"]["status_code"] == UserResponseStatusEnum.CANCELLED


@pytest.mark.unit
class TestHandleMessagePrompt:
    """Tests for __handle_message_prompt function."""

    @pytest.mark.asyncio
    async def test_handle_message_prompt_success(self):
        """Test successful message prompt handling."""
        # Test the message handling through the main handler
        mock_socket = AsyncMock()
        mock_prompt = MessagePromptRequest(
            message_id=1,
            prompt="Test message",
            timeout=30,
        )

        with patch("th_cli.test_run.prompt_manager._send_prompt_response") as mock_send:
            mock_send.return_value = asyncio.Future()
            mock_send.return_value.set_result(None)

            # Test through the main handle_prompt function
            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=mock_prompt,
                message_type="message_request",
            )

            # Verify the response was sent (indirectly tests the private function)
            mock_send.assert_called_once()
