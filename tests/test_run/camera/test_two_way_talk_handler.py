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
"""Unit tests for TwoWayTalkHandler and TwoWayTalkHTTPHandler."""

import asyncio
import json
import queue
import threading
import time
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest

import th_cli.test_run.camera.two_way_talk_handler as _module
from th_cli.test_run.camera.two_way_talk_handler import TwoWayTalkHandler, TwoWayTalkHTTPHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_http_handler(path="/", method="GET", headers=None, body=b"", server_attrs=None):
    """Build a TwoWayTalkHTTPHandler without a real socket.

    Bypasses __init__ (which parses a live HTTP request) and injects
    the attributes required by each method under test.
    """
    handler = TwoWayTalkHTTPHandler.__new__(TwoWayTalkHTTPHandler)
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
    handler._headers_sent = {}
    handler._error_code = None

    handler.send_response = lambda code, msg=None: setattr(handler, "_response_code", code)
    handler.send_header = lambda k, v: handler._headers_sent.__setitem__(k, v)
    handler.end_headers = lambda: None
    handler.send_error = lambda code, msg=None: setattr(handler, "_error_code", code)

    return handler


def _make_twt_handler(port=0):
    """Return a TwoWayTalkHandler with server patched so no real port is bound."""
    return TwoWayTalkHandler(port=port)


# ---------------------------------------------------------------------------
# TwoWayTalkHandler — init
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHandlerInit:
    """Positive: constructor stores port and initialises internal state."""

    def test_default_port(self):
        h = TwoWayTalkHandler()
        assert h.port == 8999

    def test_custom_port_stored(self):
        h = TwoWayTalkHandler(port=1234)
        assert h.port == 1234

    def test_server_initially_none(self):
        h = TwoWayTalkHandler(port=0)
        assert h._server is None

    def test_response_queue_initially_empty(self):
        h = TwoWayTalkHandler(port=0)
        assert h._response_queue.empty()

    def test_browser_ready_event_initially_clear(self):
        h = TwoWayTalkHandler(port=0)
        assert not h._browser_ready_event.is_set()


# ---------------------------------------------------------------------------
# TwoWayTalkHandler — start_waiting / start_server_only
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHandlerStart:
    """Positive: server is created and registered after start."""

    def _patched_start(self, method="start_waiting"):
        h = TwoWayTalkHandler(port=0)
        mock_srv = Mock()
        with patch("th_cli.test_run.camera.two_way_talk_handler._ReuseAddrHTTPServer") as mock_cls:
            mock_cls.return_value = mock_srv
            with patch("th_cli.test_run.camera.two_way_talk_handler.threading.Thread") as mock_thread_cls:
                mock_thread = Mock()
                mock_thread_cls.return_value = mock_thread
                with patch.object(TwoWayTalkHandler, "_free_port"):
                    getattr(h, method)()
        return h, mock_srv, mock_thread

    def test_server_thread_is_started(self):
        _, _, mock_thread = self._patched_start()
        mock_thread.start.assert_called_once()

    def test_server_attributes_initialised(self):
        _, mock_srv, _ = self._patched_start()
        assert mock_srv.prompt_ready is False
        assert mock_srv.prompt_text == "Verify two-way talk"
        assert mock_srv.prompt_options == {}

    def test_server_queues_attached(self):
        h, mock_srv, _ = self._patched_start()
        assert mock_srv.response_queue is h._response_queue
        assert mock_srv.browser_ready_event is h._browser_ready_event

    def test_start_waiting_calls_free_port(self):
        h = TwoWayTalkHandler(port=9001)
        with patch("th_cli.test_run.camera.two_way_talk_handler._ReuseAddrHTTPServer", return_value=Mock()):
            with patch("th_cli.test_run.camera.two_way_talk_handler.threading.Thread", return_value=Mock()):
                with patch.object(TwoWayTalkHandler, "_free_port") as mock_free:
                    h.start_waiting()
        mock_free.assert_called_once_with(9001)

    def test_start_server_only_does_not_call_free_port(self):
        h = TwoWayTalkHandler(port=9001)
        with patch("th_cli.test_run.camera.two_way_talk_handler._ReuseAddrHTTPServer", return_value=Mock()):
            with patch("th_cli.test_run.camera.two_way_talk_handler.threading.Thread", return_value=Mock()):
                with patch.object(TwoWayTalkHandler, "_free_port") as mock_free:
                    h.start_server_only()
        mock_free.assert_not_called()


# ---------------------------------------------------------------------------
# TwoWayTalkHandler — show_prompt / update_prompt
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHandlerShowPrompt:
    """Positive: show_prompt updates server state; no-op when server is None."""

    def _started_handler(self):
        h = TwoWayTalkHandler(port=0)
        mock_srv = Mock()
        mock_srv.prompt_ready = False
        h._server = mock_srv
        return h, mock_srv

    def test_show_prompt_sets_prompt_text(self):
        h, mock_srv = self._started_handler()
        h.show_prompt("Is it working?", {"PASS": 1, "FAIL": 2})
        assert mock_srv.prompt_text == "Is it working?"

    def test_show_prompt_sets_prompt_options(self):
        h, mock_srv = self._started_handler()
        opts = {"PASS": 1, "FAIL": 2}
        h.show_prompt("msg", opts)
        assert mock_srv.prompt_options == opts

    def test_show_prompt_sets_ready_true(self):
        h, mock_srv = self._started_handler()
        h.show_prompt("msg", {})
        assert mock_srv.prompt_ready is True

    def test_show_prompt_noop_when_server_is_none(self):
        h = TwoWayTalkHandler(port=0)
        # Must not raise
        h.show_prompt("msg", {"PASS": 1})

    def test_update_prompt_delegates_to_show_prompt(self):
        h, mock_srv = self._started_handler()
        h.update_prompt("Updated", {"PASS": 1})
        assert mock_srv.prompt_text == "Updated"
        assert mock_srv.prompt_ready is True


# ---------------------------------------------------------------------------
# TwoWayTalkHandler — wait_for_browser
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHandlerWaitForBrowser:
    """Positive + edge: wait_for_browser reflects browser_ready_event state."""

    def test_returns_true_when_event_already_set(self):
        h = TwoWayTalkHandler(port=0)
        h._browser_ready_event.set()
        assert h.wait_for_browser(timeout=1.0) is True

    def test_returns_false_on_timeout(self):
        h = TwoWayTalkHandler(port=0)
        result = h.wait_for_browser(timeout=0.05)
        assert result is False

    def test_returns_true_when_event_set_concurrently(self):
        h = TwoWayTalkHandler(port=0)

        def _set_later():
            time.sleep(0.05)
            h._browser_ready_event.set()

        threading.Thread(target=_set_later, daemon=True).start()
        assert h.wait_for_browser(timeout=2.0) is True


# ---------------------------------------------------------------------------
# TwoWayTalkHandler — wait_for_user_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHandlerWaitForUserResponse:
    """Positive + edge: async polling of response queue."""

    @pytest.mark.asyncio
    async def test_returns_queued_value_immediately(self):
        h = TwoWayTalkHandler(port=0)
        h._response_queue.put_nowait(1)
        result = await h.wait_for_user_response(timeout=1.0)
        assert result == 1

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self):
        h = TwoWayTalkHandler(port=0)
        result = await h.wait_for_user_response(timeout=0.05)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_value_queued_after_start(self):
        h = TwoWayTalkHandler(port=0)

        async def _put_later():
            await asyncio.sleep(0.05)
            h._response_queue.put_nowait(2)

        asyncio.create_task(_put_later())
        result = await h.wait_for_user_response(timeout=2.0)
        assert result == 2

    @pytest.mark.asyncio
    async def test_returns_zero_as_valid_response(self):
        h = TwoWayTalkHandler(port=0)
        h._response_queue.put_nowait(0)
        result = await h.wait_for_user_response(timeout=1.0)
        assert result == 0


# ---------------------------------------------------------------------------
# TwoWayTalkHandler — stop
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHandlerStop:
    """Positive + edge: stop shuts down server and clears server reference."""

    def test_stop_calls_server_shutdown(self):
        h = TwoWayTalkHandler(port=0)
        mock_srv = Mock()
        h._server = mock_srv

        h.stop()

        mock_srv.shutdown.assert_called_once()

    def test_stop_clears_server_reference(self):
        h = TwoWayTalkHandler(port=0)
        h._server = Mock()
        h.stop()
        assert h._server is None

    def test_stop_is_noop_when_server_is_none(self):
        h = TwoWayTalkHandler(port=0)
        h.stop()  # must not raise
        assert h._server is None

    def test_stop_clears_server_even_when_shutdown_raises(self):
        h = TwoWayTalkHandler(port=0)
        mock_srv = Mock()
        mock_srv.shutdown.side_effect = Exception("already dead")
        h._server = mock_srv
        h.stop()  # must not propagate
        assert h._server is None


# ---------------------------------------------------------------------------
# TwoWayTalkHandler — start (backward-compat alias)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHandlerStartAlias:
    """Positive: start() calls start_waiting() then show_prompt()."""

    def test_start_calls_start_waiting_and_show_prompt(self):
        h = TwoWayTalkHandler(port=0)
        with patch.object(h, "start_waiting") as mock_wait:
            with patch.object(h, "show_prompt") as mock_show:
                h.start("Verify", {"PASS": 1})
        mock_wait.assert_called_once()
        mock_show.assert_called_once_with("Verify", {"PASS": 1})


# ---------------------------------------------------------------------------
# TwoWayTalkHTTPHandler — routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkHTTPHandlerRouting:
    """Positive: GET/POST routes dispatch to correct methods."""

    def test_do_get_root_calls_serve_page(self):
        h = _make_http_handler(path="/")
        with patch.object(h, "_serve_page") as mock_fn:
            h.do_GET()
        mock_fn.assert_called_once()

    def test_do_get_with_query_string_calls_serve_page(self):
        h = _make_http_handler(path="/?nocache=123")
        with patch.object(h, "_serve_page") as mock_fn:
            h.do_GET()
        mock_fn.assert_called_once()

    def test_do_get_prompt_ready_calls_serve_prompt_ready(self):
        h = _make_http_handler(path="/prompt_ready")
        with patch.object(h, "_serve_prompt_ready") as mock_fn:
            h.do_GET()
        mock_fn.assert_called_once()

    def test_do_get_unknown_path_sends_404(self):
        h = _make_http_handler(path="/not/found")
        h.do_GET()
        assert h._error_code == 404

    def test_do_post_submit_response_calls_handle_response(self):
        h = _make_http_handler(path="/submit_response", method="POST")
        with patch.object(h, "_handle_response") as mock_fn:
            h.do_POST()
        mock_fn.assert_called_once()

    def test_do_post_browser_ready_calls_handle_browser_ready(self):
        h = _make_http_handler(path="/browser_ready", method="POST")
        with patch.object(h, "_handle_browser_ready") as mock_fn:
            h.do_POST()
        mock_fn.assert_called_once()

    def test_do_post_unknown_path_sends_404(self):
        h = _make_http_handler(path="/unknown", method="POST")
        h.do_POST()
        assert h._error_code == 404

    def test_do_options_returns_200(self):
        h = _make_http_handler(method="OPTIONS")
        h.do_OPTIONS()
        assert h._response_code == 200


# ---------------------------------------------------------------------------
# TwoWayTalkHTTPHandler — /prompt_ready JSON endpoint
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServePromptReady:
    """Positive + edge: /prompt_ready returns correct JSON payload."""

    def test_returns_ready_false_when_not_ready(self):
        h = _make_http_handler(path="/prompt_ready", server_attrs={"prompt_ready": False})
        h._serve_prompt_ready()
        assert h._response_code == 200
        body = json.loads(h.wfile.getvalue())
        assert body == {"ready": False}

    def test_returns_ready_true_with_text_and_options_when_ready(self):
        h = _make_http_handler(
            path="/prompt_ready",
            server_attrs={
                "prompt_ready": True,
                "prompt_text": "Verify audio",
                "prompt_options": {"PASS": 1, "FAIL": 2},
            },
        )
        h._serve_prompt_ready()
        body = json.loads(h.wfile.getvalue())
        assert body["ready"] is True
        assert body["prompt_text"] == "Verify audio"
        assert body["options"] == {"PASS": 1, "FAIL": 2}

    def test_content_type_header_is_json(self):
        h = _make_http_handler(path="/prompt_ready", server_attrs={"prompt_ready": False})
        h._serve_prompt_ready()
        assert h._headers_sent.get("Content-Type") == "application/json"

    def test_options_not_included_when_not_ready(self):
        h = _make_http_handler(path="/prompt_ready", server_attrs={"prompt_ready": False})
        h._serve_prompt_ready()
        body = json.loads(h.wfile.getvalue())
        assert "options" not in body
        assert "prompt_text" not in body


# ---------------------------------------------------------------------------
# TwoWayTalkHTTPHandler — /submit_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleResponse:
    """Positive + negative: /submit_response validates input and enqueues value."""

    def _make(self, body: bytes, headers: dict = None, response_queue=None):
        content_length = str(len(body))
        hdrs = {"Content-Length": content_length}
        if headers:
            hdrs.update(headers)
        srv_attrs = {}
        if response_queue is not None:
            srv_attrs["response_queue"] = response_queue
        return _make_http_handler(
            path="/submit_response",
            method="POST",
            headers=hdrs,
            body=body,
            server_attrs=srv_attrs,
        )

    def test_valid_response_enqueued_and_200_returned(self):
        resp_q = queue.Queue()
        body = json.dumps({"response": 1}).encode()
        h = self._make(body, response_queue=resp_q)
        h._handle_response()
        assert h._response_code == 200
        assert resp_q.get_nowait() == 1

    def test_response_body_is_success_json(self):
        resp_q = queue.Queue()
        body = json.dumps({"response": 2}).encode()
        h = self._make(body, response_queue=resp_q)
        h._handle_response()
        output = json.loads(h.wfile.getvalue())
        assert output == {"status": "success"}

    def test_missing_content_length_returns_400(self):
        h = _make_http_handler(
            path="/submit_response",
            method="POST",
            headers={},
            body=b"",
        )
        h._handle_response()
        assert h._error_code == 400

    def test_missing_response_key_returns_500(self):
        body = json.dumps({"other": 99}).encode()
        h = self._make(body, response_queue=queue.Queue())
        h._handle_response()
        assert h._response_code == 500

    def test_non_integer_response_value_returns_500(self):
        body = json.dumps({"response": "not-a-number"}).encode()
        h = self._make(body, response_queue=queue.Queue())
        h._handle_response()
        assert h._response_code == 500

    def test_no_response_queue_returns_500(self):
        body = json.dumps({"response": 1}).encode()
        h = _make_http_handler(
            path="/submit_response",
            method="POST",
            headers={"Content-Length": str(len(body))},
            body=body,
            server_attrs={},
        )
        h.server.response_queue = None
        h._handle_response()
        assert h._error_code == 500


# ---------------------------------------------------------------------------
# TwoWayTalkHTTPHandler — /browser_ready
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleBrowserReady:
    """Positive + edge: /browser_ready sets the threading.Event."""

    def test_sets_browser_ready_event(self):
        event = threading.Event()
        h = _make_http_handler(
            path="/browser_ready",
            method="POST",
            server_attrs={"browser_ready_event": event},
        )
        h._handle_browser_ready()
        assert event.is_set()

    def test_returns_200_ok(self):
        event = threading.Event()
        h = _make_http_handler(
            path="/browser_ready",
            method="POST",
            server_attrs={"browser_ready_event": event},
        )
        h._handle_browser_ready()
        assert h._response_code == 200

    def test_response_body_is_ok_json(self):
        event = threading.Event()
        h = _make_http_handler(
            path="/browser_ready",
            method="POST",
            server_attrs={"browser_ready_event": event},
        )
        h._handle_browser_ready()
        output = json.loads(h.wfile.getvalue())
        assert output == {"status": "ok"}

    def test_no_event_on_server_does_not_raise(self):
        h = _make_http_handler(path="/browser_ready", method="POST")
        h.server.browser_ready_event = None
        h._handle_browser_ready()  # must not raise
        assert h._response_code == 200
