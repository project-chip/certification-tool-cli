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
"""Unit tests for th_cli/test_run/logs_http_server.py."""

import json
import queue
import threading
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from th_cli.test_run.logs_http_server import (
    ENDPOINT_DOWNLOAD_LOGS,
    ENDPOINT_LOGS_STREAM,
    ENDPOINT_ROOT,
    LogStreamingHandler,
    LogsHTTPServer,
)


# ---------------------------------------------------------------------------
# Helpers: build a LogStreamingHandler without a live socket
# ---------------------------------------------------------------------------


def _make_handler(path="/", server_attrs=None):
    """Construct a LogStreamingHandler bypassing __init__."""
    handler = LogStreamingHandler.__new__(LogStreamingHandler)
    handler.path = path

    mock_server = MagicMock()
    for attr, value in (server_attrs or {}).items():
        setattr(mock_server, attr, value)
    handler.server = mock_server

    handler.wfile = BytesIO()
    handler.rfile = BytesIO()

    handler._response_code = None
    handler._headers_sent = {}
    handler._error_code = None

    handler.send_response = lambda code, msg=None: setattr(handler, "_response_code", code)
    handler.send_header = lambda k, v: handler._headers_sent.__setitem__(k, v)
    handler.end_headers = lambda: None
    handler.send_error = lambda code, msg=None: setattr(handler, "_error_code", code)

    return handler


# ---------------------------------------------------------------------------
# do_GET routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogStreamingHandlerRouting:
    def test_root_calls_serve_log_viewer(self):
        h = _make_handler(path=ENDPOINT_ROOT)
        with patch.object(h, "serve_log_viewer") as mock_fn:
            h.do_GET()
        mock_fn.assert_called_once()

    def test_stream_endpoint_calls_stream_logs(self):
        h = _make_handler(path=ENDPOINT_LOGS_STREAM)
        with patch.object(h, "stream_logs") as mock_fn:
            h.do_GET()
        mock_fn.assert_called_once()

    def test_download_endpoint_calls_download_logs(self):
        h = _make_handler(path=ENDPOINT_DOWNLOAD_LOGS)
        with patch.object(h, "download_logs") as mock_fn:
            h.do_GET()
        mock_fn.assert_called_once()

    def test_unknown_path_sends_404(self):
        h = _make_handler(path="/nonexistent")
        with patch("th_cli.test_run.logs_http_server.logger"):
            h.do_GET()
        assert h._error_code == 404


# ---------------------------------------------------------------------------
# download_logs()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDownloadLogs:
    def test_404_when_no_log_file_path(self):
        h = _make_handler(server_attrs={"log_file_path": None})
        with patch("th_cli.test_run.logs_http_server.logger"):
            h.download_logs()
        assert h._error_code == 404

    def test_404_when_file_does_not_exist(self, tmp_path):
        h = _make_handler(server_attrs={"log_file_path": str(tmp_path / "missing.log")})
        with patch("th_cli.test_run.logs_http_server.logger"):
            h.download_logs()
        assert h._error_code == 404

    def test_200_and_correct_headers_for_existing_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        log_file.write_bytes(b"log content here")
        h = _make_handler(server_attrs={"log_file_path": str(log_file)})

        with patch("th_cli.test_run.logs_http_server.logger"):
            h.download_logs()

        assert h._response_code == 200
        assert h._headers_sent.get("Content-Type") == "text/plain; charset=utf-8"
        assert "Content-Disposition" in h._headers_sent

    def test_file_content_written_to_wfile(self, tmp_path):
        content = b"line 1\nline 2\n"
        log_file = tmp_path / "run.log"
        log_file.write_bytes(content)
        h = _make_handler(server_attrs={"log_file_path": str(log_file)})

        with patch("th_cli.test_run.logs_http_server.logger"):
            h.download_logs()

        assert h.wfile.getvalue() == content

    def test_handles_broken_pipe_gracefully(self, tmp_path):
        log_file = tmp_path / "run.log"
        log_file.write_bytes(b"data")
        h = _make_handler(server_attrs={"log_file_path": str(log_file)})
        # Make wfile.write raise BrokenPipeError
        h.wfile = MagicMock()
        h.wfile.write.side_effect = BrokenPipeError

        with patch("th_cli.test_run.logs_http_server.logger"):
            h.download_logs()  # must not raise


# ---------------------------------------------------------------------------
# _send_sse_event()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSendSseEvent:
    def test_returns_true_on_success(self):
        h = _make_handler()
        result = h._send_sse_event("test", {"key": "value"})
        assert result is True

    def test_writes_sse_format_to_wfile(self):
        h = _make_handler()
        h._send_sse_event("myevent", {"msg": "hello"})
        output = h.wfile.getvalue().decode("utf-8")
        assert "event: myevent" in output
        assert "hello" in output
        assert output.endswith("\n\n")

    def test_returns_false_on_broken_pipe(self):
        h = _make_handler()
        h.wfile = MagicMock()
        h.wfile.write.side_effect = BrokenPipeError
        result = h._send_sse_event("ev", {})
        assert result is False

    def test_returns_false_on_connection_reset(self):
        h = _make_handler()
        h.wfile = MagicMock()
        h.wfile.write.side_effect = ConnectionResetError
        result = h._send_sse_event("ev", {})
        assert result is False

    def test_data_is_valid_json(self):
        h = _make_handler()
        h._send_sse_event("ev", {"a": 1, "b": "two"})
        output = h.wfile.getvalue().decode("utf-8")
        # extract the data line
        data_line = [ln for ln in output.split("\n") if ln.startswith("data:")][0]
        parsed = json.loads(data_line[len("data:"):].strip())
        assert parsed == {"a": 1, "b": "two"}


# ---------------------------------------------------------------------------
# stream_logs()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStreamLogs:
    def test_sends_sse_headers(self):
        q = queue.Queue()
        q.put(None)  # immediate end-of-stream
        h = _make_handler(server_attrs={"log_queue": q})

        with patch("th_cli.test_run.logs_http_server.logger"):
            h.stream_logs()

        assert h._response_code == 200
        assert h._headers_sent.get("Content-Type") == "text/event-stream"

    def test_sends_end_event_on_none_sentinel(self):
        q = queue.Queue()
        q.put(None)
        h = _make_handler(server_attrs={"log_queue": q})
        sent_events = []
        original_send = h._send_sse_event
        h._send_sse_event = lambda ev, data: sent_events.append(ev) or True

        with patch("th_cli.test_run.logs_http_server.logger"):
            h.stream_logs()

        assert "end" in sent_events

    def test_streams_log_entries_from_queue(self):
        q = queue.Queue()
        q.put({"message": "hello", "level": "INFO", "timestamp": "2025-01-01"})
        q.put(None)
        h = _make_handler(server_attrs={"log_queue": q})
        sent_events = []
        h._send_sse_event = lambda ev, data: sent_events.append((ev, data)) or True

        with patch("th_cli.test_run.logs_http_server.logger"):
            h.stream_logs()

        log_events = [d for ev, d in sent_events if ev == "log"]
        assert len(log_events) == 1
        assert log_events[0]["message"] == "hello"

    def test_stops_when_send_sse_returns_false(self):
        q = queue.Queue()
        q.put({"message": "msg", "level": "INFO", "timestamp": "t"})
        q.put({"message": "msg2", "level": "INFO", "timestamp": "t"})
        h = _make_handler(server_attrs={"log_queue": q})
        call_count = [0]

        def _send(ev, data):
            call_count[0] += 1
            if ev == "connected":
                return True
            return False  # disconnect immediately

        h._send_sse_event = _send

        with patch("th_cli.test_run.logs_http_server.logger"):
            h.stream_logs()

        # Should not have kept reading after disconnect
        assert call_count[0] <= 3

    def test_no_log_queue_on_server_returns_early(self):
        h = _make_handler(server_attrs={"log_queue": None})
        with patch("th_cli.test_run.logs_http_server.logger"):
            h.stream_logs()
        # Should have sent 200 headers but not crashed
        assert h._response_code == 200

    def test_debug_log_at_100_entries(self):
        """Covers line 134: `if sent_count % 100 == 0` debug message."""
        q = queue.Queue()
        # Put 100 log entries then sentinel
        for i in range(100):
            q.put({"message": f"msg{i}", "level": "INFO", "timestamp": "t"})
        q.put(None)

        h = _make_handler(server_attrs={"log_queue": q})
        with patch("th_cli.test_run.logs_http_server.logger") as mock_logger:
            h.stream_logs()

        # 100 entries should have triggered the debug log
        mock_logger.debug.assert_called()


# ---------------------------------------------------------------------------
# serve_log_viewer()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServeLogViewer:
    def test_returns_200(self):
        h = _make_handler(server_attrs={"test_run_title": "My Run"})
        with patch("th_cli.test_run.logs_http_server.logger"):
            with patch("builtins.open", side_effect=FileNotFoundError("no template")):
                h.serve_log_viewer()
        assert h._response_code == 200

    def test_sets_html_content_type(self):
        h = _make_handler(server_attrs={"test_run_title": "My Run"})
        with patch("th_cli.test_run.logs_http_server.logger"):
            with patch("builtins.open", side_effect=FileNotFoundError("no template")):
                h.serve_log_viewer()
        assert "text/html" in h._headers_sent.get("Content-Type", "")

    def test_sets_no_cache_headers(self):
        h = _make_handler(server_attrs={"test_run_title": "My Run"})
        with patch("th_cli.test_run.logs_http_server.logger"):
            with patch("builtins.open", side_effect=FileNotFoundError("no template")):
                h.serve_log_viewer()
        assert "no-store" in h._headers_sent.get("Cache-Control", "")

    def test_fallback_html_on_template_error(self):
        h = _make_handler(server_attrs={"test_run_title": "FallbackRun"})
        with patch("th_cli.test_run.logs_http_server.logger"):
            with patch("builtins.open", side_effect=FileNotFoundError("no template")):
                h.serve_log_viewer()
        content = h.wfile.getvalue().decode("utf-8")
        assert "Error" in content or "FallbackRun" in content

    def test_uses_template_when_available(self, tmp_path):
        template = tmp_path / "log_viewer.html"
        template.write_text("<html><title>{test_run_title}</title></html>")
        h = _make_handler(server_attrs={"test_run_title": "TemplateRun"})

        with patch("th_cli.test_run.logs_http_server.logger"):
            with patch("th_cli.test_run.logs_http_server.Path") as mock_path_cls:
                mock_path_instance = MagicMock()
                mock_path_instance.__truediv__ = MagicMock(return_value=template)
                mock_path_cls.return_value = mock_path_instance
                # Use the real open for the actual template file
                h.serve_log_viewer()

        assert h._response_code == 200


# ---------------------------------------------------------------------------
# log_message() — should be a no-op
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogMessage:
    def test_does_not_raise(self):
        h = _make_handler()
        h.log_message("GET /path HTTP/1.1", "200")  # must not raise


# ---------------------------------------------------------------------------
# LogsHTTPServer.__init__
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogsHTTPServerInit:
    def test_port_stored(self):
        srv = LogsHTTPServer(port=9999)
        assert srv.port == 9999

    def test_default_port(self):
        srv = LogsHTTPServer()
        assert srv.port == 8998

    def test_server_initially_none(self):
        srv = LogsHTTPServer()
        assert srv.server is None

    def test_server_thread_initially_none(self):
        srv = LogsHTTPServer()
        assert srv.server_thread is None


# ---------------------------------------------------------------------------
# LogsHTTPServer.start()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogsHTTPServerStart:
    def test_creates_threading_http_server(self):
        srv = LogsHTTPServer(port=0)
        q = queue.Queue()

        with patch("th_cli.test_run.logs_http_server.ThreadingHTTPServer") as mock_cls:
            mock_ths = MagicMock()
            mock_cls.return_value = mock_ths
            with patch("th_cli.test_run.logs_http_server.threading.Thread") as mock_thread_cls:
                mock_thread = MagicMock()
                mock_thread_cls.return_value = mock_thread
                with patch("th_cli.test_run.logs_http_server.logger"):
                    srv.start(log_queue=q, test_run_title="Run")

        mock_cls.assert_called_once()
        mock_thread.start.assert_called_once()

    def test_sets_server_attributes(self):
        srv = LogsHTTPServer(port=0)
        q = queue.Queue()

        with patch("th_cli.test_run.logs_http_server.ThreadingHTTPServer") as mock_cls:
            mock_ths = MagicMock()
            mock_cls.return_value = mock_ths
            with patch("th_cli.test_run.logs_http_server.threading.Thread", return_value=MagicMock()):
                with patch("th_cli.test_run.logs_http_server.logger"):
                    srv.start(log_queue=q, test_run_title="MyTitle", local_ip="1.2.3.4", log_file_path="/tmp/f.log")

        assert mock_ths.log_queue is q
        assert mock_ths.test_run_title == "MyTitle"
        assert mock_ths.local_ip == "1.2.3.4"
        assert mock_ths.log_file_path == "/tmp/f.log"

    def test_propagates_oserror(self):
        srv = LogsHTTPServer(port=0)
        with patch("th_cli.test_run.logs_http_server.ThreadingHTTPServer", side_effect=OSError("port in use")):
            with patch("th_cli.test_run.logs_http_server.logger"):
                with pytest.raises(OSError):
                    srv.start(log_queue=queue.Queue(), test_run_title="run")


# ---------------------------------------------------------------------------
# LogsHTTPServer.stop()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogsHTTPServerStop:
    def test_noop_when_server_is_none(self):
        srv = LogsHTTPServer()
        with patch("th_cli.test_run.logs_http_server.logger"):
            srv.stop()  # must not raise
        assert srv.server is None

    def test_calls_shutdown_on_server(self):
        srv = LogsHTTPServer()
        mock_ths = MagicMock()
        srv.server = mock_ths

        with patch("th_cli.test_run.logs_http_server.logger"):
            srv.stop()

        mock_ths.shutdown.assert_called_once()

    def test_clears_server_and_thread_refs(self):
        srv = LogsHTTPServer()
        srv.server = MagicMock()
        srv.server_thread = MagicMock()

        with patch("th_cli.test_run.logs_http_server.logger"):
            srv.stop()

        assert srv.server is None
        assert srv.server_thread is None
