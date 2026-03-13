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

import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from th_cli.shared_constants import MessageTypeEnum
from th_cli.test_run import prompt_manager
from th_cli.test_run.socket_schemas import (
    ImageVerificationPromptRequest,
    MessagePromptRequest,
    PromptRequest,
    PushAVStreamVerificationRequest,
    TextInputPromptRequest,
    TwoWayTalkVerificationRequest,
    UserResponseStatusEnum,
)

# ---------------------------------------------------------------------------
# _get_local_ip
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetLocalIp:
    def test_returns_detected_ip(self):
        with patch("socket.socket") as mock_socket_cls:
            mock_sock = MagicMock()
            mock_sock.getsockname.return_value = ("192.168.1.100", 12345)
            mock_socket_cls.return_value.__enter__.return_value = mock_sock

            result = prompt_manager._get_local_ip()

        assert result == "192.168.1.100"
        mock_sock.connect.assert_called_once_with(("8.8.8.8", 80))

    def test_falls_back_to_localhost_on_error(self):
        with patch("socket.socket") as mock_socket_cls:
            mock_socket_cls.return_value.__enter__.side_effect = Exception("Network error")

            result = prompt_manager._get_local_ip()

        assert result == "localhost"


# ---------------------------------------------------------------------------
# _get_video_handler
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetVideoHandler:
    def test_creates_instance_on_first_call(self):
        prompt_manager._video_handler_instance = None

        with patch("th_cli.test_run.camera.CameraStreamHandler") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            result = prompt_manager._get_video_handler()

        assert result is mock_instance
        mock_cls.assert_called_once()

    def test_reuses_existing_instance(self):
        mock_instance = MagicMock()
        prompt_manager._video_handler_instance = mock_instance

        with patch("th_cli.test_run.camera.CameraStreamHandler") as mock_cls:
            result = prompt_manager._get_video_handler()

        assert result is mock_instance
        mock_cls.assert_not_called()


# ---------------------------------------------------------------------------
# _cleanup_video_handler
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCleanupVideoHandler:
    @pytest.mark.asyncio
    async def test_calls_stop_on_existing_instance(self):
        mock_instance = MagicMock()
        mock_instance.stop_video_capture_and_stream = AsyncMock()
        prompt_manager._video_handler_instance = mock_instance

        await prompt_manager._cleanup_video_handler()

        mock_instance.stop_video_capture_and_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_noop_when_no_instance(self):
        prompt_manager._video_handler_instance = None
        await prompt_manager._cleanup_video_handler()  # must not raise

    @pytest.mark.asyncio
    async def test_errors_are_silently_ignored(self):
        mock_instance = MagicMock()
        mock_instance.stop_video_capture_and_stream = AsyncMock(side_effect=Exception("fail"))
        prompt_manager._video_handler_instance = mock_instance

        await prompt_manager._cleanup_video_handler()  # must not raise


# ---------------------------------------------------------------------------
# handle_prompt — routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandlePromptRouting:

    @pytest.mark.asyncio
    async def test_image_verification_routes_to_image_handler(self):
        mock_socket = AsyncMock()
        request = ImageVerificationPromptRequest(
            message_id=1,
            prompt="Verify image",
            timeout=30,
            options={"PASS": 1, "FAIL": 2},
            image_hex_str="ffd8ffe0",
        )
        with patch(
            "th_cli.test_run.prompt_manager._handle_image_verification_prompt",
            new_callable=AsyncMock,
        ) as mock_handler:
            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=request,
                message_type=MessageTypeEnum.IMAGE_VERIFICATION_REQUEST,
            )
        mock_handler.assert_called_once_with(socket=mock_socket, prompt=request)

    @pytest.mark.asyncio
    async def test_push_av_stream_routes_to_push_av_handler(self):
        mock_socket = AsyncMock()
        request = PushAVStreamVerificationRequest(
            message_id=3,
            prompt="Verify Push AV",
            timeout=120,
            options={"PASS": 1, "FAIL": 2},
        )
        with patch(
            "th_cli.test_run.prompt_manager._handle_push_av_stream_prompt",
            new_callable=AsyncMock,
        ) as mock_handler:
            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=request,
                message_type=MessageTypeEnum.PUSH_AV_STREAM_VERIFICATION_REQUEST,
            )
        mock_handler.assert_called_once_with(socket=mock_socket, prompt=request)

    @pytest.mark.asyncio
    async def test_message_request_sends_ack_response(self):
        mock_socket = AsyncMock()
        request = MessagePromptRequest(message_id=4, prompt="Acknowledge this", timeout=30)

        with patch(
            "th_cli.test_run.prompt_manager._send_prompt_response",
            new_callable=AsyncMock,
        ) as mock_send:
            await prompt_manager.handle_prompt(
                socket=mock_socket,
                request=request,
                message_type=MessageTypeEnum.MESSAGE_REQUEST,
            )

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == "ACK"
        assert mock_send.call_args[1]["prompt"] is request

    @pytest.mark.asyncio
    async def test_unknown_request_type_does_not_raise(self):
        mock_socket = AsyncMock()
        request = PromptRequest(message_id=99, prompt="?", timeout=10)

        with patch("click.echo"):
            await prompt_manager.handle_prompt(socket=mock_socket, request=request)


# ---------------------------------------------------------------------------
# _send_prompt_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSendPromptResponse:

    @pytest.mark.asyncio
    async def test_sends_json_with_correct_structure(self):
        mock_socket = AsyncMock()
        mock_prompt = Mock()
        mock_prompt.message_id = 123

        await prompt_manager._send_prompt_response(
            socket=mock_socket,
            prompt=mock_prompt,
            response="hello",
            status_code=UserResponseStatusEnum.OKAY,
        )

        mock_socket.send.assert_called_once()
        payload = json.loads(mock_socket.send.call_args[0][0])
        assert payload["type"] == "prompt_response"
        assert payload["payload"]["response"] == "hello"
        assert payload["payload"]["status_code"] == UserResponseStatusEnum.OKAY
        assert payload["payload"]["message_id"] == 123

    @pytest.mark.asyncio
    async def test_cancelled_status_code_is_preserved(self):
        mock_socket = AsyncMock()
        mock_prompt = Mock()
        mock_prompt.message_id = 456

        await prompt_manager._send_prompt_response(
            socket=mock_socket,
            prompt=mock_prompt,
            response="cancelled",
            status_code=UserResponseStatusEnum.CANCELLED,
        )

        payload = json.loads(mock_socket.send.call_args[0][0])
        assert payload["payload"]["status_code"] == UserResponseStatusEnum.CANCELLED

    @pytest.mark.asyncio
    async def test_integer_response_value_is_sent(self):
        mock_socket = AsyncMock()
        mock_prompt = Mock()
        mock_prompt.message_id = 1

        await prompt_manager._send_prompt_response(
            socket=mock_socket,
            prompt=mock_prompt,
            response=2,
        )

        payload = json.loads(mock_socket.send.call_args[0][0])
        assert payload["payload"]["response"] == 2


# ---------------------------------------------------------------------------
# __valid_text_input — tested via handle_prompt → __handle_text_prompt
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidTextInput:

    @pytest.mark.asyncio
    async def test_accepts_input_when_no_regex_pattern(self):
        prompt = TextInputPromptRequest(
            message_id=1,
            prompt="Enter something",
            timeout=30,
            regex_pattern=None,
        )
        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("aioconsole.ainput", new_callable=AsyncMock, return_value="anything"):
                await prompt_manager.handle_prompt(socket=AsyncMock(), request=prompt)

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == "anything"

    @pytest.mark.asyncio
    async def test_accepts_input_matching_regex(self):
        prompt = TextInputPromptRequest(
            message_id=1,
            prompt="Enter digits",
            timeout=30,
            regex_pattern=r"^\d+$",
        )
        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("aioconsole.ainput", new_callable=AsyncMock, return_value="12345"):
                await prompt_manager.handle_prompt(socket=AsyncMock(), request=prompt)

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == "12345"

    @pytest.mark.asyncio
    async def test_retries_until_valid_input(self):
        prompt = TextInputPromptRequest(
            message_id=1,
            prompt="Enter digits",
            timeout=30,
            regex_pattern=r"^\d+$",
        )
        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("aioconsole.ainput", new_callable=AsyncMock, side_effect=["not-digits", "9999"]):
                with patch("click.echo"):
                    await prompt_manager.handle_prompt(socket=AsyncMock(), request=prompt)

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == "9999"

    @pytest.mark.asyncio
    async def test_uses_default_value_when_input_is_empty(self):
        prompt = TextInputPromptRequest(
            message_id=1,
            prompt="Enter value",
            timeout=30,
            default_value="mydefault",
            regex_pattern=None,
        )
        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("aioconsole.ainput", new_callable=AsyncMock, return_value=""):
                with patch("click.echo"):
                    await prompt_manager.handle_prompt(socket=AsyncMock(), request=prompt)

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == "mydefault"


# ---------------------------------------------------------------------------
# __valid_file_upload — tested via handle_file_upload_request
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidFileUpload:

    @pytest.mark.asyncio
    async def test_accepts_txt_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"hello")
            tmp_path = f.name

        try:
            with patch(
                "th_cli.test_run.prompt_manager.__upload_file_and_send_response",
                new_callable=AsyncMock,
            ) as mock_upload:
                with patch("aioconsole.ainput", new_callable=AsyncMock, return_value=tmp_path):
                    with patch("click.echo"):
                        await prompt_manager.handle_file_upload_request(
                            socket=AsyncMock(),
                            request=MagicMock(prompt="Upload file", timeout=30),
                        )

            mock_upload.assert_called_once()
            assert mock_upload.call_args[1]["file_path"] == tmp_path
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_empty_input_skips_upload(self):
        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("aioconsole.ainput", new_callable=AsyncMock, return_value=""):
                with patch("click.echo"):
                    await prompt_manager.handle_file_upload_request(
                        socket=AsyncMock(),
                        request=MagicMock(prompt="Upload", timeout=30, message_id=1),
                    )

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == ""


# ---------------------------------------------------------------------------
# _handle_two_way_talk_prompt (via handle_prompt dispatch)
# ---------------------------------------------------------------------------


def _make_two_way_talk_prompt(**kwargs):
    """Build a minimal TwoWayTalkVerificationRequest."""
    defaults = dict(
        prompt="Verify if two way talk is working",
        options={"PASS": 1, "FAIL": 2},
        timeout=10,
        message_id=99,
    )
    defaults.update(kwargs)
    return TwoWayTalkVerificationRequest(**defaults)


@pytest.mark.unit
class TestHandleTwoWayTalkPrompt:
    """Tests for _handle_two_way_talk_prompt dispatched via handle_prompt."""

    def _make_handler(self, response=1):
        mock_handler = AsyncMock()
        mock_handler.wait_for_user_response = AsyncMock(return_value=response)
        mock_handler.show_prompt = Mock()
        mock_handler.stop = Mock()
        return mock_handler

    @pytest.mark.asyncio
    async def test_uses_injected_handler(self):
        """When a handler is injected, it should be used directly."""
        prompt = _make_two_way_talk_prompt()
        mock_handler = self._make_handler(response=1)

        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock):
            with patch("click.echo"):
                await prompt_manager.handle_prompt(
                    socket=AsyncMock(),
                    request=prompt,
                    message_type=MessageTypeEnum.TWO_WAY_TALK_VERIFICATION_REQUEST,
                    two_way_talk_handler=mock_handler,
                )

        mock_handler.show_prompt.assert_called_once_with(prompt_text=prompt.prompt, prompt_options=prompt.options)

    @pytest.mark.asyncio
    async def test_sends_response_for_pass_selection(self):
        """Selected PASS option is forwarded to backend."""
        prompt = _make_two_way_talk_prompt()
        mock_handler = self._make_handler(response=1)  # PASS = 1

        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("click.echo"):
                await prompt_manager.handle_prompt(
                    socket=AsyncMock(),
                    request=prompt,
                    message_type=MessageTypeEnum.TWO_WAY_TALK_VERIFICATION_REQUEST,
                    two_way_talk_handler=mock_handler,
                )

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == 1

    @pytest.mark.asyncio
    async def test_stop_called_after_response(self):
        """handler.stop() must always be called after wait_for_user_response."""
        prompt = _make_two_way_talk_prompt()
        mock_handler = self._make_handler(response=2)  # FAIL = 2

        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock):
            with patch("click.echo"):
                await prompt_manager.handle_prompt(
                    socket=AsyncMock(),
                    request=prompt,
                    message_type=MessageTypeEnum.TWO_WAY_TALK_VERIFICATION_REQUEST,
                    two_way_talk_handler=mock_handler,
                )

        mock_handler.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_called_even_on_timeout(self):
        """handler.stop() must be called even when wait_for_user_response returns None."""
        prompt = _make_two_way_talk_prompt()
        mock_handler = self._make_handler(response=None)

        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("click.echo"):
                await prompt_manager.handle_prompt(
                    socket=AsyncMock(),
                    request=prompt,
                    message_type=MessageTypeEnum.TWO_WAY_TALK_VERIFICATION_REQUEST,
                    two_way_talk_handler=mock_handler,
                )

        mock_handler.stop.assert_called_once()
        mock_send.assert_not_called()  # no response sent on timeout

    @pytest.mark.asyncio
    async def test_fallback_handler_created_when_no_handler_injected(self):
        """When no handler is injected, a fallback TwoWayTalkHandler is created with start_server_only."""
        prompt = _make_two_way_talk_prompt()
        mock_fallback = AsyncMock()
        mock_fallback.wait_for_user_response = AsyncMock(return_value=1)
        mock_fallback.show_prompt = Mock()
        mock_fallback.stop = Mock()
        mock_fallback.start_server_only = Mock()

        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock):
            with patch("th_cli.test_run.prompt_manager.TwoWayTalkHandler", return_value=mock_fallback) as mock_cls:
                with patch("click.echo"):
                    await prompt_manager.handle_prompt(
                        socket=AsyncMock(),
                        request=prompt,
                        message_type=MessageTypeEnum.TWO_WAY_TALK_VERIFICATION_REQUEST,
                        two_way_talk_handler=None,
                    )

        mock_cls.assert_called_once_with(port=8999)
        mock_fallback.start_server_only.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatched_via_isinstance_when_no_message_type(self):
        """Dispatch works via isinstance check when message_type is not provided."""
        prompt = _make_two_way_talk_prompt()
        mock_handler = self._make_handler(response=1)

        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("click.echo"):
                await prompt_manager.handle_prompt(
                    socket=AsyncMock(),
                    request=prompt,
                    message_type=None,
                    two_way_talk_handler=mock_handler,
                )

        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_extension_retries_then_skip(self):
        with patch("th_cli.test_run.prompt_manager._send_prompt_response", new_callable=AsyncMock) as mock_send:
            with patch("aioconsole.ainput", new_callable=AsyncMock, side_effect=["/some/file.exe", ""]):
                with patch("click.echo"):
                    await prompt_manager.handle_file_upload_request(
                        socket=AsyncMock(),
                        request=MagicMock(prompt="Upload", timeout=30, message_id=1),
                    )

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["response"] == ""
