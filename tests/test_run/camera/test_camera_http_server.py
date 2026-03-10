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

import json
import queue
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from th_cli.test_run.camera.camera_http_server import CameraHTTPServer, VideoStreamingHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler(path="/", method="GET", headers=None, body=b"", server_attrs=None):
    """Build a VideoStreamingHandler instance without a real socket.

    Bypasses __init__ entirely (which would try to parse an HTTP request)
    and injects the attributes we care about manually.
    """
    handler = VideoStreamingHandler.__new__(VideoStreamingHandler)

    # Minimal mock request / client address
    handler.path = path
    handler.command = method

    # Mock headers as a dict-like object
    mock_headers = MagicMock()
    mock_headers.__contains__ = lambda self, key: key in (headers or {})
    mock_headers.__getitem__ = lambda self, key: (headers or {})[key]
    mock_headers.get = lambda key, default=None: (headers or {}).get(key, default)
    handler.headers = mock_headers

    # Readable body
    handler.rfile = BytesIO(body)

    # Writable output buffer
    handler.wfile = BytesIO()

    # Mock server with configurable attributes
    mock_server = MagicMock()
    for attr, value in (server_attrs or {}).items():
        setattr(mock_server, attr, value)
    handler.server = mock_server

    # Stub out send_response / send_header / end_headers / send_error
    # so we can inspect what was sent without a real socket
    handler._response_code = None
    handler._headers_sent = {}
    handler._error_code = None

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
# CameraHTTPServer
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCameraHTTPServerInit:
    """Tests for CameraHTTPServer.__init__."""

    def test_default_port(self):
        server = CameraHTTPServer()
        assert server.port == 8999

    def test_custom_port(self):
        server = CameraHTTPServer(port=9001)
        assert server.port == 9001

    def test_server_and_thread_initially_none(self):
        server = CameraHTTPServer()
        assert server.server is None
        assert server.server_thread is None


@pytest.mark.unit
class TestCameraHTTPServerStart:
    """Tests for CameraHTTPServer.start."""

    def _start(self, server, **kwargs):
        defaults = dict(
            mp4_queue=queue.Queue(),
            response_queue=queue.Queue(),
            video_handler=Mock(),
            prompt_options={"PASS": 1, "FAIL": 2},
            prompt_text="Test prompt",
            local_ip="192.168.1.1",
        )
        defaults.update(kwargs)
        with patch("th_cli.test_run.camera.camera_http_server.ThreadingHTTPServer") as mock_cls:
            mock_srv = Mock()
            mock_cls.return_value = mock_srv
            with patch("th_cli.test_run.camera.camera_http_server.threading.Thread") as mock_thread_cls:
                mock_thread = Mock()
                mock_thread_cls.return_value = mock_thread
                server.start(**defaults)
                return mock_srv, mock_thread

    def test_server_attributes_set_correctly(self):
        server = CameraHTTPServer(port=0)
        mp4_q = queue.Queue()
        resp_q = queue.Queue()
        mock_srv, _ = self._start(
            server,
            mp4_queue=mp4_q,
            response_queue=resp_q,
            prompt_options={"PASS": 1},
            prompt_text="Hello",
            local_ip="10.0.0.1",
        )
        assert mock_srv.mp4_queue is mp4_q
        assert mock_srv.response_queue is resp_q
        assert mock_srv.prompt_options == {"PASS": 1}
        assert mock_srv.prompt_text == "Hello"
        assert mock_srv.local_ip == "10.0.0.1"
        assert mock_srv.allow_reuse_address is True

    def test_none_prompt_options_defaults_to_empty_dict(self):
        server = CameraHTTPServer(port=0)
        mock_srv, _ = self._start(server, prompt_options=None)
        assert mock_srv.prompt_options == {}

    def test_none_local_ip_defaults_to_localhost(self):
        server = CameraHTTPServer(port=0)
        mock_srv, _ = self._start(server, local_ip=None)
        assert mock_srv.local_ip == "localhost"

    def test_thread_is_started(self):
        server = CameraHTTPServer(port=0)
        _, mock_thread = self._start(server)
        mock_thread.start.assert_called_once()

    def test_server_and_thread_stored_on_instance(self):
        server = CameraHTTPServer(port=0)
        mock_srv, mock_thread = self._start(server)
        assert server.server is mock_srv
        assert server.server_thread is mock_thread

    def test_push_av_flags_set(self):
        server = CameraHTTPServer(port=0)
        mock_srv, _ = self._start(
            server,
            is_push_av_verification=True,
            push_av_server_url="https://device:1234",
        )
        assert mock_srv.is_push_av_verification is True
        assert mock_srv.push_av_server_url == "https://device:1234"

    def test_start_raises_on_server_creation_failure(self):
        server = CameraHTTPServer(port=0)
        with patch(
            "th_cli.test_run.camera.camera_http_server.ThreadingHTTPServer",
            side_effect=OSError("address in use"),
        ):
            with pytest.raises(OSError):
                server.start(
                    mp4_queue=queue.Queue(),
                    response_queue=queue.Queue(),
                    video_handler=None,
                )


@pytest.mark.unit
class TestCameraHTTPServerStop:
    """Tests for CameraHTTPServer.stop."""

    def test_stop_calls_shutdown_and_clears_references(self):
        server = CameraHTTPServer()
        mock_srv = Mock()
        server.server = mock_srv
        server.server_thread = Mock()

        server.stop()

        mock_srv.shutdown.assert_called_once()
        assert server.server is None
        assert server.server_thread is None

    def test_stop_is_noop_when_not_started(self):
        server = CameraHTTPServer()
        server.stop()  # must not raise
        assert server.server is None

    def test_stop_clears_state_even_when_shutdown_raises(self):
        server = CameraHTTPServer()
        mock_srv = Mock()
        mock_srv.shutdown.side_effect = Exception("already dead")
        server.server = mock_srv
        server.server_thread = Mock()

        server.stop()  # must not propagate

        assert server.server is None
        assert server.server_thread is None


# ---------------------------------------------------------------------------
# VideoStreamingHandler routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoStreamingHandlerRouting:
    """Tests for do_GET and do_POST routing in VideoStreamingHandler."""

    def test_do_get_root_calls_serve_player(self):
        handler = _make_handler(path="/")
        with patch.object(handler, "serve_player") as mock_serve:
            handler.do_GET()
        mock_serve.assert_called_once()

    def test_do_get_video_live_calls_stream_live_video(self):
        handler = _make_handler(path="/video_live.mp4")
        with patch.object(handler, "stream_live_video") as mock_stream:
            handler.do_GET()
        mock_stream.assert_called_once()

    def test_do_get_api_streams_calls_handle_streams_api(self):
        handler = _make_handler(path="/api/streams")
        with patch.object(handler, "handle_streams_api") as mock_streams:
            handler.do_GET()
        mock_streams.assert_called_once()

    def test_do_get_api_stream_proxy_calls_handle_stream_proxy(self):
        handler = _make_handler(path="/api/stream_proxy?url=http://x/y")
        with patch.object(handler, "handle_stream_proxy") as mock_proxy:
            handler.do_GET()
        mock_proxy.assert_called_once()

    def test_do_get_proxy_path_calls_handle_simple_proxy(self):
        handler = _make_handler(path="/proxy/abc123")
        with patch.object(handler, "handle_simple_proxy") as mock_simple:
            handler.do_GET()
        mock_simple.assert_called_once()

    def test_do_get_unknown_path_sends_404(self):
        handler = _make_handler(path="/not/a/real/path")
        handler.do_GET()
        assert handler._error_code == 404

    def test_do_get_strips_query_string_for_routing(self):
        """Query parameters must not break routing to serve_player."""
        handler = _make_handler(path="/?nocache=1234")
        with patch.object(handler, "serve_player") as mock_serve:
            handler.do_GET()
        mock_serve.assert_called_once()

    def test_do_post_submit_response_calls_handle_response(self):
        handler = _make_handler(path="/submit_response", method="POST")
        with patch.object(handler, "handle_response") as mock_resp:
            handler.do_POST()
        mock_resp.assert_called_once()

    def test_do_post_unknown_path_sends_404(self):
        handler = _make_handler(path="/unknown", method="POST")
        handler.do_POST()
        assert handler._error_code == 404


# ---------------------------------------------------------------------------
# VideoStreamingHandler.handle_response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleResponse:
    """Tests for VideoStreamingHandler.handle_response — the only method with
    substantial custom logic that can be unit-tested without a live network."""

    def _make(self, body: bytes, headers: dict = None, response_queue=None):
        content_length = str(len(body))
        hdrs = {"Content-Length": content_length}
        if headers:
            hdrs.update(headers)
        srv_attrs = {}
        if response_queue is not None:
            srv_attrs["response_queue"] = response_queue
        handler = _make_handler(
            path="/submit_response",
            method="POST",
            headers=hdrs,
            body=body,
            server_attrs=srv_attrs,
        )
        return handler

    def test_valid_response_queued_and_200_returned(self):
        resp_q = queue.Queue()
        body = json.dumps({"response": 1}).encode()
        handler = self._make(body, response_queue=resp_q)

        handler.handle_response()

        assert handler._response_code == 200
        assert resp_q.get_nowait() == 1

    def test_missing_content_length_header_returns_400(self):
        handler = _make_handler(
            path="/submit_response",
            method="POST",
            headers={},  # no Content-Length
            body=b"",
        )
        handler.handle_response()
        assert handler._error_code == 400

    def test_invalid_json_returns_400(self):
        body = b"not json at all"
        handler = self._make(body, response_queue=queue.Queue())
        handler.handle_response()
        assert handler._response_code == 400
        output = json.loads(handler.wfile.getvalue())
        assert "Invalid JSON" in output["error"]

    def test_missing_response_key_returns_400(self):
        body = json.dumps({"other_key": 42}).encode()
        handler = self._make(body, response_queue=queue.Queue())
        handler.handle_response()
        assert handler._response_code == 400

    def test_non_integer_response_value_returns_400(self):
        body = json.dumps({"response": "not-a-number"}).encode()
        handler = self._make(body, response_queue=queue.Queue())
        handler.handle_response()
        assert handler._response_code == 400

    def test_no_response_queue_on_server_returns_500(self):
        body = json.dumps({"response": 1}).encode()
        # server_attrs has no response_queue key → getattr returns None
        handler = _make_handler(
            path="/submit_response",
            method="POST",
            headers={"Content-Length": str(len(body))},
            body=body,
            server_attrs={},
        )
        # Make sure getattr(server, "response_queue", None) returns None
        handler.server.response_queue = None
        handler.handle_response()
        assert handler._error_code == 500

    def test_full_response_queue_returns_500(self):
        full_q = queue.Queue(maxsize=1)
        full_q.put_nowait(99)  # fill it
        body = json.dumps({"response": 1}).encode()
        handler = self._make(body, response_queue=full_q)
        handler.handle_response()
        assert handler._error_code == 500

    def test_success_response_body_is_valid_json(self):
        resp_q = queue.Queue()
        body = json.dumps({"response": 2}).encode()
        handler = self._make(body, response_queue=resp_q)
        handler.handle_response()
        output = json.loads(handler.wfile.getvalue())
        assert output == {"status": "success"}
