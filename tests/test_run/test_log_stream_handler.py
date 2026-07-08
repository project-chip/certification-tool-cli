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


# ---------------------------------------------------------------------------
# stop() — error path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogStreamHandlerStopError:
    def test_logs_error_when_http_server_stop_raises(self):
        h, mock_srv = _make_handler()
        h.is_running = True
        mock_srv.stop.side_effect = RuntimeError("stop failed")
        with patch("th_cli.test_run.log_stream_handler.logger") as mock_logger:
            h.stop()
        mock_logger.error.assert_called()


# ---------------------------------------------------------------------------
# init_tree()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInitTree:
    def test_noop_when_not_running(self):
        h, _ = _make_handler()
        h.is_running = False
        with patch.object(h, "_broadcast") as mock_bcast:
            h.init_tree(MagicMock())
        mock_bcast.assert_not_called()

    def test_broadcasts_tree_init_event(self):
        h, _ = _make_handler()
        h.is_running = True
        client_q = queue.Queue()
        h._clients.add(client_q)
        run = MagicMock()
        run.title = "My Run"
        run.test_suite_executions = []
        with patch("th_cli.test_run.log_stream_handler.logger"):
            h.init_tree(run)
        event = client_q.get_nowait()
        assert event["type"] == "tree_init"
        assert "data" in event

    def test_updates_tree_state_in_place(self):
        h, _ = _make_handler()
        h.is_running = True
        run = MagicMock()
        run.title = "Run Title"
        run.test_suite_executions = []
        with patch("th_cli.test_run.log_stream_handler.logger"):
            h.init_tree(run)
        assert h.tree_state.get("title") == "Run Title"

    def test_handles_build_exception_silently(self):
        h, _ = _make_handler()
        h.is_running = True
        with patch.object(h, "_build_tree", side_effect=RuntimeError("fail")):
            with patch("th_cli.test_run.log_stream_handler.logger"):
                h.init_tree(MagicMock())  # must not raise


# ---------------------------------------------------------------------------
# update_tree_node()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUpdateTreeNode:
    def test_noop_when_not_running(self):
        h, _ = _make_handler()
        h.is_running = False
        with patch.object(h, "_broadcast") as mock_bcast:
            h.update_tree_node(state="passed")
        mock_bcast.assert_not_called()

    def test_run_level_update(self):
        h, _ = _make_handler()
        h.is_running = True
        h.tree_state = {"state": "pending", "suites": []}
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.update_tree_node(state="executing")
        assert h.tree_state["state"] == "executing"
        event = client_q.get_nowait()
        assert event["node_type"] == "run"
        assert event["state"] == "executing"

    def test_suite_level_update(self):
        h, _ = _make_handler()
        h.is_running = True
        h.tree_state = {"suites": [{"state": "pending", "cases": []}]}
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.update_tree_node(state="passed", suite_idx=0)
        assert h.tree_state["suites"][0]["state"] == "passed"
        event = client_q.get_nowait()
        assert event["node_type"] == "suite"

    def test_case_level_update(self):
        h, _ = _make_handler()
        h.is_running = True
        h.tree_state = {"suites": [{"cases": [{"state": "pending", "steps": []}]}]}
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.update_tree_node(state="failed", suite_idx=0, case_idx=0)
        assert h.tree_state["suites"][0]["cases"][0]["state"] == "failed"
        event = client_q.get_nowait()
        assert event["node_type"] == "case"

    def test_step_level_update(self):
        h, _ = _make_handler()
        h.is_running = True
        h.tree_state = {"suites": [{"cases": [{"steps": [{"state": "pending"}]}]}]}
        client_q = queue.Queue()
        h._clients.add(client_q)
        h.update_tree_node(state="passed", suite_idx=0, case_idx=0, step_idx=0)
        assert h.tree_state["suites"][0]["cases"][0]["steps"][0]["state"] == "passed"
        event = client_q.get_nowait()
        assert event["node_type"] == "step"

    def test_tolerates_index_error_on_invalid_tree_state(self):
        h, _ = _make_handler()
        h.is_running = True
        h.tree_state = {}  # missing expected structure
        h.update_tree_node(state="passed", suite_idx=99)  # must not raise


# ---------------------------------------------------------------------------
# _build_tree()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildTree:
    def test_minimal_run_no_suites(self):
        h, _ = _make_handler()
        run = MagicMock()
        run.title = "My Run"
        run.state = MagicMock(value="pending")
        run.test_suite_executions = []
        tree = h._build_tree(run)
        assert tree["title"] == "My Run"
        assert tree["suites"] == []

    def test_builds_suite_case_step_hierarchy(self):
        h, _ = _make_handler()

        step = MagicMock()
        step.title = "Step 1"
        step.state = MagicMock(value="pending")

        case = MagicMock()
        case.test_case_metadata.title = "Case 1"
        case.test_case_metadata.public_id = "TC-1"
        case.state = MagicMock(value="pending")
        case.test_step_executions = [step]

        suite = MagicMock()
        suite.test_suite_metadata.title = "Suite 1"
        suite.state = MagicMock(value="pending")
        suite.test_case_executions = [case]

        run = MagicMock()
        run.title = "Run"
        run.state = MagicMock(value="executing")
        run.test_suite_executions = [suite]

        tree = h._build_tree(run)
        assert len(tree["suites"]) == 1
        assert tree["suites"][0]["title"] == "Suite 1"
        assert len(tree["suites"][0]["cases"]) == 1
        assert len(tree["suites"][0]["cases"][0]["steps"]) == 1
        assert tree["suites"][0]["cases"][0]["steps"][0]["title"] == "Step 1"

    def test_falls_back_to_default_titles_when_metadata_none(self):
        h, _ = _make_handler()

        case = MagicMock()
        case.test_case_metadata = None
        case.state = MagicMock(value="pending")
        case.test_step_executions = []

        suite = MagicMock()
        suite.test_suite_metadata = None
        suite.state = MagicMock(value="pending")
        suite.test_case_executions = [case]

        run = MagicMock()
        run.title = "Run"
        run.state = MagicMock(value="pending")
        run.test_suite_executions = [suite]

        tree = h._build_tree(run)
        assert "Suite 0" in tree["suites"][0]["title"]
        assert "Case 0" in tree["suites"][0]["cases"][0]["title"]


# ---------------------------------------------------------------------------
# _get_state()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetState:
    def test_returns_pending_when_state_is_none(self):
        h, _ = _make_handler()
        obj = MagicMock()
        obj.state = None
        assert h._get_state(obj) == "pending"

    def test_returns_state_value_for_enum_like_object(self):
        h, _ = _make_handler()
        obj = MagicMock()
        obj.state = MagicMock(value="executing")
        assert h._get_state(obj) == "executing"

    def test_returns_str_state_when_no_value_attr(self):
        h, _ = _make_handler()
        obj = MagicMock()
        obj.state = "passed"  # plain string — no .value attribute
        assert h._get_state(obj) == "passed"

    def test_returns_pending_on_exception(self):
        h, _ = _make_handler()

        class BrokenState:
            @property
            def value(self):
                raise RuntimeError("broken")

        obj = MagicMock()
        obj.state = BrokenState()
        assert h._get_state(obj) == "pending"

