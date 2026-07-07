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
"""Unit tests for th_cli/test_run/log_stream_handler.py."""

import queue
import socket
from unittest.mock import MagicMock, patch

import pytest

from th_cli.test_run.log_stream_handler import LogStreamHandler


# ---------------------------------------------------------------------------
# LogStreamHandler.__init__
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogStreamHandlerInit:
    def test_port_stored(self):
        with patch("th_cli.test_run.log_stream_handler.LogsHTTPServer"):
            h = LogStreamHandler(port=9000)
        assert h.port == 9000

    def test_default_port(self):
        with patch("th_cli.test_run.log_stream_handler.LogsHTTPServer"):
            h = LogStreamHandler()
        assert h.port == 8998

    def test_is_running_initially_false(self):
        with patch("th_cli.test_run.log_stream_handler.LogsHTTPServer"):
            h = LogStreamHandler()
        assert h.is_running is False

    def test_clients_is_empty_set(self):
        with patch("th_cli.test_run.log_stream_handler.LogsHTTPServer"):
            h = LogStreamHandler()
        assert isinstance(h._clients, set)
        assert len(h._clients) == 0

    def test_log_file_path_initially_none(self):
        with patch("th_cli.test_run.log_stream_handler.LogsHTTPServer"):
            h = LogStreamHandler()
        assert h.log_file_path is None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler(port=8998):
    """Create a LogStreamHandler with a mocked LogsHTTPServer."""
    with patch("th_cli.test_run.log_stream_handler.LogsHTTPServer") as mock_cls:
        mock_srv = MagicMock()
        mock_cls.return_value = mock_srv
        h = LogStreamHandler(port=port)
    h.http_server = mock_srv
    return h, mock_srv


# ---------------------------------------------------------------------------
# start()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogStreamHandlerStart:
    def test_sets_is_running_true(self):
        h, mock_srv = _make_handler()
        with patch.object(h, "_get_local_ip", return_value="10.0.0.1"):
            with patch("th_cli.test_run.log_stream_handler.logger"):
                h.start(test_run_title="Test Run")
        assert h.is_running is True

    def test_returns_url_with_local_ip_and_port(self):
        h, mock_srv = _make_handler(port=9001)
        with patch.object(h, "_get_local_ip", return_value="192.168.1.5"):
            with patch("th_cli.test_run.log_stream_handler.logger"):
                url = h.start(test_run_title="My Run")
        assert "192.168.1.5" in url
        assert "9001" in url

    def test_calls_http_server_start(self):
        h, mock_srv = _make_handler()
        with patch.object(h, "_get_local_ip", return_value="10.0.0.1"):
            with patch("th_cli.test_run.log_stream_handler.logger"):
                h.start(test_run_title="run", log_file_path="/tmp/test.log")
        mock_srv.start.assert_called_once()

    def test_stores_log_file_path(self):
        h, mock_srv = _make_handler()
        with patch.object(h, "_get_local_ip", return_value="10.0.0.1"):
            with patch("th_cli.test_run.log_stream_handler.logger"):
                h.start(test_run_title="run", log_file_path="/var/log/test.log")
        assert h.log_file_path == "/var/log/test.log"

    def test_already_running_returns_url_without_restart(self):
        h, mock_srv = _make_handler()
        h.is_running = True

        with patch.object(h, "_get_local_ip", return_value="10.0.0.2"):
            with patch("th_cli.test_run.log_stream_handler.logger"):
                url = h.start(test_run_title="run")

        mock_srv.start.assert_not_called()
        assert url  # URL returned

    def test_propagates_exception_from_server_start(self):
        h, mock_srv = _make_handler()
        mock_srv.start.side_effect = OSError("port in use")

        with patch.object(h, "_get_local_ip", return_value="10.0.0.1"):
            with patch("th_cli.test_run.log_stream_handler.logger"):
                with pytest.raises(OSError):
                    h.start(test_run_title="run")

        assert h.is_running is False


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogStreamHandlerStop:
    def test_noop_when_not_running(self):
        h, mock_srv = _make_handler()
        h.is_running = False
        with patch("th_cli.test_run.log_stream_handler.logger"):
            h.stop()
        mock_srv.stop.assert_not_called()

    def test_calls_http_server_stop(self):
        h, mock_srv = _make_handler()
        h.is_running = True

        with patch("th_cli.test_run.log_stream_handler.logger"):
            h.stop()

        mock_srv.stop.assert_called_once()

    def test_sets_is_running_false(self):
        h, mock_srv = _make_handler()
        h.is_running = True

        with patch("th_cli.test_run.log_stream_handler.logger"):
            h.stop()

        assert h.is_running is False

    def test_broadcasts_none_sentinel_on_stop(self):
        h, mock_srv = _make_handler()
        h.is_running = True
        client_q = queue.Queue()
        h._clients.add(client_q)

        with patch("th_cli.test_run.log_stream_handler.logger"):
            h.stop()

        assert client_q.get_nowait() is None

    def test_stop_does_not_raise_when_client_queue_full(self):
        h, mock_srv = _make_handler()
        h.is_running = True
        client_q = queue.Queue(maxsize=1)
        client_q.put_nowait("existing")  # fill to capacity
        h._clients.add(client_q)

        with patch("th_cli.test_run.log_stream_handler.logger"):
            h.stop()  # must not raise


# ---------------------------------------------------------------------------
# add_log_entry()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAddLogEntry:
    def test_noop_when_not_running(self):
        h, _ = _make_handler()
        h.is_running = False
        with patch.object(h, "_broadcast") as mock_bcast:
            h.add_log_entry(message="ignored")
        mock_bcast.assert_not_called()

    def test_adds_entry_to_queue_when_running(self):
        h, _ = _make_handler()
        h.is_running = True
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.add_log_entry(message="hello", level="INFO")
        entry = client_q.get_nowait()
        assert entry["message"] == "hello"
        assert entry["level"] == "INFO"

    def test_auto_generates_timestamp_when_not_provided(self):
        h, _ = _make_handler()
        h.is_running = True
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.add_log_entry(message="msg")
        entry = client_q.get_nowait()
        assert "timestamp" in entry
        assert entry["timestamp"] is not None

    def test_uses_provided_timestamp(self):
        h, _ = _make_handler()
        h.is_running = True
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.add_log_entry(message="msg", timestamp="2025-01-01T00:00:00")
        entry = client_q.get_nowait()
        assert entry["timestamp"] == "2025-01-01T00:00:00"

    def test_level_uppercased(self):
        h, _ = _make_handler()
        h.is_running = True
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.add_log_entry(message="msg", level="warning")
        entry = client_q.get_nowait()
        assert entry["level"] == "WARNING"

    def test_silently_drops_when_queue_full(self):
        h, _ = _make_handler()
        h.is_running = True
        client_q = queue.Queue(maxsize=1)
        client_q.put_nowait({"message": "x"})  # fill to capacity
        h._clients.add(client_q)
        h.add_log_entry(message="overflow")  # must not raise


# ---------------------------------------------------------------------------
# _get_local_ip()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetLocalIp:
    def test_returns_ip_string_on_success(self):
        h, _ = _make_handler()
        mock_socket = MagicMock()
        mock_socket.getsockname.return_value = ("192.168.0.10", 0)

        with patch("th_cli.test_run.log_stream_handler.socket.socket", return_value=mock_socket):
            result = h._get_local_ip()

        assert result == "192.168.0.10"

    def test_returns_localhost_on_socket_error(self):
        h, _ = _make_handler()
        with patch("th_cli.test_run.log_stream_handler.socket.socket", side_effect=OSError("no network")):
            result = h._get_local_ip()
        assert result == "localhost"

    def test_closes_socket_after_use(self):
        h, _ = _make_handler()
        mock_socket = MagicMock()
        mock_socket.getsockname.return_value = ("10.0.0.1", 0)

        with patch("th_cli.test_run.log_stream_handler.socket.socket", return_value=mock_socket):
            h._get_local_ip()

        mock_socket.close.assert_called_once()


# ---------------------------------------------------------------------------
# _get_log_viewer_url()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetLogViewerUrl:
    def test_returns_http_url_with_port(self):
        h, _ = _make_handler(port=8998)
        with patch.object(h, "_get_local_ip", return_value="10.1.2.3"):
            url = h._get_log_viewer_url()
        assert url == "http://10.1.2.3:8998"

    def test_uses_local_ip(self):
        h, _ = _make_handler(port=9000)
        with patch.object(h, "_get_local_ip", return_value="172.16.0.5"):
            url = h._get_log_viewer_url()
        assert "172.16.0.5" in url
