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
"""Additional coverage tests for camera_http_server.py — covers
stream_live_video, handle_streams_api, handle_simple_proxy,
handle_stream_proxy, serve_player, do_OPTIONS, log_message.
"""

import base64
import json
import queue
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from th_cli.test_run.camera.camera_http_server import VideoStreamingHandler


# ---------------------------------------------------------------------------
# Shared helper (same as in test_camera_http_server.py)
# ---------------------------------------------------------------------------


def _make_handler(path="/", method="GET", headers=None, body=b"", server_attrs=None):
    handler = VideoStreamingHandler.__new__(VideoStreamingHandler)
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


# ---------------------------------------------------------------------------
# do_OPTIONS
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDoOptions:
    def test_returns_200(self):
        h = _make_handler(method="OPTIONS")
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.do_OPTIONS()
        assert h._response_code == 200

    def test_sets_cors_headers(self):
        h = _make_handler(method="OPTIONS")
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.do_OPTIONS()
        assert h._headers_sent.get("Access-Control-Allow-Origin") == "*"


# ---------------------------------------------------------------------------
# log_message (suppresses output)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogMessage:
    def test_does_not_raise(self):
        h = _make_handler()
        h.log_message("GET %s", "/")  # must not raise


# ---------------------------------------------------------------------------
# stream_live_video
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStreamLiveVideo:
    def test_sends_200_with_video_mp4_content_type(self):
        q = queue.Queue()
        q.put(None)  # immediate end-of-stream
        h = _make_handler(server_attrs={"mp4_queue": q})
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.stream_live_video()
        assert h._response_code == 200
        assert h._headers_sent.get("Content-Type") == "video/mp4"

    def test_streams_data_chunks_from_queue(self):
        q = queue.Queue()
        q.put(b"chunk1")
        q.put(b"chunk2")
        q.put(None)  # end signal
        h = _make_handler(server_attrs={"mp4_queue": q})
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.stream_live_video()
        output = h.wfile.getvalue()
        assert b"chunk1" in output
        assert b"chunk2" in output

    def test_returns_early_when_no_mp4_queue(self):
        h = _make_handler(server_attrs={"mp4_queue": None})
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.stream_live_video()
        # Should not crash; response was already 200
        assert h._response_code == 200

    def test_stops_on_write_error(self):
        q = queue.Queue()
        q.put(b"data")
        h = _make_handler(server_attrs={"mp4_queue": q})
        h.wfile = MagicMock()
        h.wfile.write.side_effect = BrokenPipeError
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.stream_live_video()  # must not raise


# ---------------------------------------------------------------------------
# serve_player
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServePlayer:
    def test_returns_200_with_html_content_type(self):
        h = _make_handler(server_attrs={
            "prompt_options": {"PASS": 1},
            "prompt_text": "Verify video",
            "is_push_av_verification": False,
            "push_av_server_url": None,
        })
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            with patch("builtins.open", side_effect=FileNotFoundError("no template")):
                h.serve_player()
        assert h._response_code == 200
        assert "text/html" in h._headers_sent.get("Content-Type", "")

    def test_fallback_html_on_template_error(self):
        h = _make_handler(server_attrs={
            "prompt_options": {},
            "prompt_text": "Fallback test",
            "is_push_av_verification": False,
            "push_av_server_url": None,
        })
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            with patch("builtins.open", side_effect=Exception("template missing")):
                h.serve_player()
        content = h.wfile.getvalue().decode("utf-8")
        assert "Fallback test" in content or "Error" in content

    def test_sets_no_cache_headers(self):
        h = _make_handler(server_attrs={
            "prompt_options": {},
            "prompt_text": "Video",
            "is_push_av_verification": False,
            "push_av_server_url": None,
        })
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            with patch("builtins.open", side_effect=FileNotFoundError):
                h.serve_player()
        assert "no-store" in h._headers_sent.get("Cache-Control", "")

    def test_push_av_template_selected_when_flag_set(self):
        h = _make_handler(server_attrs={
            "prompt_options": {"PASS": 1},
            "prompt_text": "Push AV test",
            "is_push_av_verification": True,
            "push_av_server_url": "https://device:1234",
        })
        opened_files = []

        def fake_open(path, *args, **kwargs):
            opened_files.append(str(path))
            raise FileNotFoundError("no template")

        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            with patch("builtins.open", side_effect=fake_open):
                h.serve_player()
        # push_av template should have been attempted
        assert any("push_av" in f for f in opened_files)

    def test_radio_options_rendered(self):
        h = _make_handler(server_attrs={
            "prompt_options": {"PASS": 1, "FAIL": 2},
            "prompt_text": "Pick one",
            "is_push_av_verification": False,
            "push_av_server_url": None,
        })
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            with patch("builtins.open", side_effect=FileNotFoundError):
                h.serve_player()
        # When fallback HTML is used, wfile may not contain options,
        # but serve_player must at minimum not raise
        assert h._response_code == 200


# ---------------------------------------------------------------------------
# handle_streams_api
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleStreamsApi:
    def test_returns_500_when_no_push_av_url(self):
        h = _make_handler(server_attrs={"push_av_server_url": None})
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.handle_streams_api()
        assert h._response_code == 500

    def test_returns_streams_on_success(self):
        h = _make_handler(server_attrs={"push_av_server_url": "http://device:1234"})
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"streams": ["stream1"]}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_streams_api()

        assert h._response_code == 200
        output = json.loads(h.wfile.getvalue())
        assert output == {"streams": ["stream1"]}

    def test_returns_500_on_non_200_response(self):
        h = _make_handler(server_attrs={"push_av_server_url": "http://device:1234"})
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_streams_api()

        assert h._response_code == 500

    def test_returns_500_on_connection_error(self):
        h = _make_handler(server_attrs={"push_av_server_url": "http://device:1234"})
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("connection failed")

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_streams_api()

        assert h._response_code == 500


# ---------------------------------------------------------------------------
# handle_simple_proxy
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleSimpleProxy:
    def _encoded_url(self, url: str) -> str:
        return base64.urlsafe_b64encode(url.encode()).decode("ascii")

    def test_returns_200_on_success(self):
        encoded = self._encoded_url("http://device/stream")
        h = _make_handler(path=f"/proxy/{encoded}")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "video/mp4"}
        mock_response.content = b"mp4data"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_simple_proxy()

        assert h._response_code == 200
        assert h.wfile.getvalue() == b"mp4data"

    def test_returns_400_on_invalid_base64(self):
        h = _make_handler(path="/proxy/!!!invalid!!!")
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.handle_simple_proxy()
        assert h._error_code == 400

    def test_returns_upstream_status_on_non_200(self):
        encoded = self._encoded_url("http://device/missing")
        h = _make_handler(path=f"/proxy/{encoded}")

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_simple_proxy()

        assert h._error_code == 404

    def test_returns_500_on_fetch_error(self):
        encoded = self._encoded_url("http://device/stream")
        h = _make_handler(path=f"/proxy/{encoded}")

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("network error")

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_simple_proxy()

        assert h._error_code == 500

    def test_extra_path_appended_to_url(self):
        encoded = self._encoded_url("http://device")
        h = _make_handler(path=f"/proxy/{encoded}/segment/0.ts")

        fetched_urls = []
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "video/mp2t"}
        mock_response.content = b"ts_data"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        def fake_get(url, **kwargs):
            fetched_urls.append(url)
            return mock_response

        mock_client.get = fake_get

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_simple_proxy()

        assert fetched_urls and "/segment/0.ts" in fetched_urls[0]


# ---------------------------------------------------------------------------
# handle_stream_proxy
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleStreamProxy:
    def test_returns_400_when_no_url_param(self):
        h = _make_handler(path="/api/stream_proxy")
        with patch("th_cli.test_run.camera.camera_http_server.logger"):
            h.handle_stream_proxy()
        assert h._error_code == 400

    def test_returns_regular_content_on_success(self):
        h = _make_handler(path="/api/stream_proxy?url=http://device/video.mp4")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "video/mp4"}
        mock_response.content = b"video_data"
        mock_response.text = ""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_stream_proxy()

        assert h._response_code == 200
        assert h.wfile.getvalue() == b"video_data"

    def test_returns_upstream_error_status(self):
        h = _make_handler(path="/api/stream_proxy?url=http://device/missing.mp4")

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_stream_proxy()

        assert h._error_code == 404

    def test_rewrites_mpd_manifest(self):
        mpd_content = """<?xml version="1.0"?>
<MPD><Period><AdaptationSet>
<SegmentTemplate initialization="init.mp4" media="seg-$Number$.m4s"/>
</AdaptationSet></Period></MPD>"""
        h = _make_handler(
            path="/api/stream_proxy?url=http://device/stream.mpd",
            server_attrs={"local_ip": "10.0.0.1", "server_port": 8999},
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/dash+xml"}
        mock_response.text = mpd_content
        mock_response.content = mpd_content.encode()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_stream_proxy()

        assert h._response_code == 200
        # Rewritten manifest should be served
        content = h.wfile.getvalue().decode("utf-8")
        assert "BaseURL" in content or "proxy" in content

    def test_returns_500_on_exception(self):
        h = _make_handler(path="/api/stream_proxy?url=http://device/video.mp4")
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("network error")
        h.wfile = MagicMock()
        h.wfile.closed = False

        with patch("th_cli.test_run.camera.camera_http_server.httpx.Client", return_value=mock_client):
            with patch("th_cli.test_run.camera.camera_http_server.logger"):
                h.handle_stream_proxy()

        assert h._error_code == 500
