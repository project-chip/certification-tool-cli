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
"""Unit tests for image_handler module."""

import asyncio
import json
import queue
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from th_cli.test_run.camera.image_handler import ImageVerificationHandler, ImageVerificationHTTPHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_http_handler(path="/", method="GET", headers=None, body=b"", server_attrs=None):
    """Construct an ImageVerificationHTTPHandler without a live socket."""
    handler = ImageVerificationHTTPHandler.__new__(ImageVerificationHTTPHandler)
    handler.path = path
    handler.command = method

    mock_headers = MagicMock()
    mock_headers.__contains__ = lambda self, key: key in (headers or {})
    mock_headers.__getitem__ = lambda self, key: (headers or {})[key]
    mock_headers.get = lambda key, default=None: (headers or {}).get(key, default)
    handler.headers = mock_headers

    handler.rfile = BytesIO(body)
    handler.wfile = BytesIO()

    mock_server = MagicMock()
    for attr, value in (server_attrs or {}).items():
        setattr(mock_server, attr, value)
    handler.server = mock_server

    handler._response_code = None
    handler._error_code = None
    handler._headers_sent = {}

    def _send_response(code, message=None):
        handler._response_code = code

    def _send_header(key, value):
        handler._headers_sent[key] = value

    def _end_headers():
        pass

    def _send_error(code, message=None):
        handler._error_code = code

    handler.send_response = _send_response
    handler.send_header = _send_header
    handler.end_headers = _end_headers
    handler.send_error = _send_error

    return handler


# ---------------------------------------------------------------------------
# ImageVerificationHTTPHandler routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImageVerificationHTTPHandlerRouting:
    """Tests for do_GET and do_POST routing."""

    def test_get_root_calls_serve_page(self):
        handler = _make_http_handler(path="/")
        with patch.object(handler, "_serve_page") as mock_serve:
            handler.do_GET()
        mock_serve.assert_called_once()

    def test_get_image_calls_serve_image(self):
        handler = _make_http_handler(path="/image")
        with patch.object(handler, "_serve_image") as mock_img:
            handler.do_GET()
        mock_img.assert_called_once()

    def test_get_unknown_path_sends_404(self):
        handler = _make_http_handler(path="/unknown")
        handler.do_GET()
        assert handler._error_code == 404

    def test_post_submit_response_calls_handle_response(self):
        handler = _make_http_handler(path="/submit_response", method="POST")
        with patch.object(handler, "_handle_response") as mock_resp:
            handler.do_POST()
        mock_resp.assert_called_once()

    def test_post_unknown_path_sends_404(self):
        handler = _make_http_handler(path="/other", method="POST")
        handler.do_POST()
        assert handler._error_code == 404


# ---------------------------------------------------------------------------
# ImageVerificationHTTPHandler._serve_image
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServeImage:
    """Tests for ImageVerificationHTTPHandler._serve_image."""

    def test_serves_image_data_with_200(self):
        image_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        handler = _make_http_handler(server_attrs={"image_data": image_bytes})
        handler._serve_image()
        assert handler._response_code == 200
        assert handler._headers_sent.get("Content-Type") == "image/jpeg"
        assert handler._headers_sent.get("Content-Length") == str(len(image_bytes))
        assert handler.wfile.getvalue() == image_bytes

    def test_returns_404_when_no_image_data(self):
        handler = _make_http_handler(server_attrs={"image_data": None})
        handler._serve_image()
        assert handler._error_code == 404

    def test_returns_404_when_image_data_empty(self):
        handler = _make_http_handler(server_attrs={"image_data": b""})
        handler._serve_image()
        assert handler._error_code == 404


# ---------------------------------------------------------------------------
# ImageVerificationHTTPHandler._handle_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHTTPHandlerHandleResponse:
    """Tests for ImageVerificationHTTPHandler._handle_response."""

    def _make(self, body: bytes, response_queue=None):
        srv_attrs = {}
        if response_queue is not None:
            srv_attrs["response_queue"] = response_queue
        hdrs = {"Content-Length": str(len(body))}
        return _make_http_handler(
            path="/submit_response",
            method="POST",
            headers=hdrs,
            body=body,
            server_attrs=srv_attrs,
        )

    def test_valid_response_queued_and_200_returned(self):
        resp_q = queue.Queue()
        handler = self._make(json.dumps({"response": 1}).encode(), response_queue=resp_q)
        handler._handle_response()
        assert handler._response_code == 200
        assert resp_q.get_nowait() == 1

    def test_success_response_body_is_valid_json(self):
        resp_q = queue.Queue()
        handler = self._make(json.dumps({"response": 2}).encode(), response_queue=resp_q)
        handler._handle_response()
        output = json.loads(handler.wfile.getvalue())
        assert output == {"status": "success"}

    def test_invalid_json_returns_400(self):
        handler = self._make(b"not-json", response_queue=queue.Queue())
        handler._handle_response()
        assert handler._response_code == 400

    def test_missing_response_key_returns_400(self):
        body = json.dumps({"wrong_key": 1}).encode()
        handler = self._make(body, response_queue=queue.Queue())
        handler._handle_response()
        assert handler._response_code == 400

    def test_non_integer_response_value_returns_400(self):
        body = json.dumps({"response": "abc"}).encode()
        handler = self._make(body, response_queue=queue.Queue())
        handler._handle_response()
        assert handler._response_code == 400

    def test_no_response_queue_still_returns_200(self):
        """When response_queue is absent the value is silently dropped, not an error."""
        handler = _make_http_handler(
            path="/submit_response",
            method="POST",
            headers={"Content-Length": "16"},
            body=json.dumps({"response": 1}).encode(),
        )
        handler.server.response_queue = None
        handler._handle_response()
        assert handler._response_code == 200


# ---------------------------------------------------------------------------
# ImageVerificationHandler.__init__ and set_prompt_data
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImageVerificationHandlerInit:
    def test_default_port(self):
        assert ImageVerificationHandler().port == 8999

    def test_custom_port(self):
        assert ImageVerificationHandler(port=9090).port == 9090

    def test_http_server_and_thread_initially_none(self):
        h = ImageVerificationHandler()
        assert h.http_server is None
        assert h._server_thread is None

    def test_response_queue_is_queue(self):
        assert isinstance(ImageVerificationHandler()._response_queue, queue.Queue)


@pytest.mark.unit
class TestSetPromptData:
    def test_stores_all_three_fields(self):
        h = ImageVerificationHandler()
        h.set_prompt_data("Verify", {"PASS": 1}, b"\xff\xd8")
        assert h._prompt_text == "Verify"
        assert h._options == {"PASS": 1}
        assert h._image_data == b"\xff\xd8"


# ---------------------------------------------------------------------------
# ImageVerificationHandler.start_image_server
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStartImageServer:

    @pytest.mark.asyncio
    async def test_creates_server_with_correct_attributes(self):
        h = ImageVerificationHandler(port=0)
        h.set_prompt_data("Prompt", {"PASS": 1}, b"\xff\xd8")

        with patch("th_cli.test_run.camera.image_handler.ThreadingHTTPServer") as mock_cls:
            mock_srv = MagicMock()
            mock_cls.return_value = mock_srv
            with patch("th_cli.test_run.camera.image_handler.threading.Thread") as mock_thread_cls:
                mock_thread = MagicMock()
                mock_thread_cls.return_value = mock_thread
                await h.start_image_server()

        assert mock_srv.allow_reuse_address is True
        assert mock_srv.image_data == b"\xff\xd8"
        assert mock_srv.prompt_text == "Prompt"
        assert mock_srv.prompt_options == {"PASS": 1}
        assert mock_srv.response_queue is h._response_queue
        mock_thread.start.assert_called_once()
        assert h.http_server is mock_srv
        assert h._server_thread is mock_thread

    @pytest.mark.asyncio
    async def test_default_prompt_text_when_not_set(self):
        h = ImageVerificationHandler(port=0)
        h._image_data = b"\xff\xd8"  # skip set_prompt_data

        with patch("th_cli.test_run.camera.image_handler.ThreadingHTTPServer") as mock_cls:
            mock_srv = MagicMock()
            mock_cls.return_value = mock_srv
            with patch("th_cli.test_run.camera.image_handler.threading.Thread"):
                await h.start_image_server()

        assert mock_srv.prompt_text == "Verify the snapshot image"

    @pytest.mark.asyncio
    async def test_default_prompt_options_when_not_set(self):
        h = ImageVerificationHandler(port=0)
        h._image_data = b"\xff\xd8"

        with patch("th_cli.test_run.camera.image_handler.ThreadingHTTPServer") as mock_cls:
            mock_srv = MagicMock()
            mock_cls.return_value = mock_srv
            with patch("th_cli.test_run.camera.image_handler.threading.Thread"):
                await h.start_image_server()

        assert mock_srv.prompt_options == {}


# ---------------------------------------------------------------------------
# ImageVerificationHandler.wait_for_user_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWaitForUserResponse:

    @pytest.mark.asyncio
    async def test_returns_pre_queued_response_immediately(self):
        h = ImageVerificationHandler()
        h._response_queue.put_nowait(1)
        assert await h.wait_for_user_response(timeout=1.0) == 1

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self):
        h = ImageVerificationHandler()
        assert await h.wait_for_user_response(timeout=0.15) is None

    @pytest.mark.asyncio
    async def test_returns_response_enqueued_during_poll(self):
        h = ImageVerificationHandler()

        async def enqueue_later():
            await asyncio.sleep(0.05)
            h._response_queue.put_nowait(2)

        results = await asyncio.gather(enqueue_later(), h.wait_for_user_response(timeout=1.0))
        assert results[1] == 2


# ---------------------------------------------------------------------------
# ImageVerificationHandler.stop_image_server
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStopImageServer:

    def test_calls_shutdown_and_clears_state(self):
        h = ImageVerificationHandler()
        mock_srv = MagicMock()
        h.http_server = mock_srv
        h._server_thread = Mock()
        h.stop_image_server()
        mock_srv.shutdown.assert_called_once()
        assert h.http_server is None
        assert h._server_thread is None

    def test_noop_when_not_started(self):
        h = ImageVerificationHandler()
        h.stop_image_server()  # must not raise
        assert h.http_server is None

    def test_clears_state_even_when_shutdown_raises(self):
        h = ImageVerificationHandler()
        mock_srv = MagicMock()
        mock_srv.shutdown.side_effect = Exception("already dead")
        h.http_server = mock_srv
        h._server_thread = Mock()
        h.stop_image_server()
        assert h.http_server is None
        assert h._server_thread is None
