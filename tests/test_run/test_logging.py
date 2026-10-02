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
"""Unit tests for th_cli/test_run/logging.py."""

import time
from unittest.mock import MagicMock, call, patch

import pytest

import th_cli.test_run.logging as logging_module
from th_cli.test_run.logging import (
    configure_logger_for_run,
    get_log_stream_url,
    stop_log_streaming,
)
from th_cli.test_run.socket_schemas import TestLogRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_global_handler():
    """Reset the module-level _log_stream_handler to None between tests."""
    logging_module._log_stream_handler = None


# ---------------------------------------------------------------------------
# configure_logger_for_run — without streaming
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfigureLoggerForRunNoStreaming:
    def setup_method(self):
        _reset_global_handler()

    def test_returns_string_path(self):
        with patch("th_cli.test_run.logging.logger"):
            result = configure_logger_for_run("my_run")
        assert isinstance(result, str)

    def test_path_contains_run_title(self):
        with patch("th_cli.test_run.logging.logger"):
            result = configure_logger_for_run("special_run_title")
        assert "special_run_title" in result

    def test_log_handler_remains_none_when_streaming_disabled(self):
        with patch("th_cli.test_run.logging.logger"):
            configure_logger_for_run("run", enable_log_streaming=False)
        assert logging_module._log_stream_handler is None

    def test_logger_remove_called(self):
        with patch("th_cli.test_run.logging.logger") as mock_logger:
            configure_logger_for_run("run")
        mock_logger.remove.assert_called_once()

    def test_logger_add_called_with_path(self):
        with patch("th_cli.test_run.logging.logger") as mock_logger:
            result = configure_logger_for_run("run")
        # logger.add(log_path, ...) — first positional arg is the path
        add_calls = mock_logger.add.call_args_list
        assert len(add_calls) >= 1
        first_call_path = add_calls[0][0][0]
        assert "run" in first_call_path


# ---------------------------------------------------------------------------
# configure_logger_for_run — with streaming
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfigureLoggerForRunWithStreaming:
    def setup_method(self):
        _reset_global_handler()

    def test_sets_global_handler_when_streaming_enabled(self):
        mock_handler = MagicMock()
        mock_handler.start.return_value = "http://1.2.3.4:8998"
        mock_handler.is_running = True

        with patch("th_cli.test_run.logging.logger"):
            with patch("th_cli.test_run.log_stream_handler.LogStreamHandler", return_value=mock_handler):
                configure_logger_for_run("run", enable_log_streaming=True)

        assert logging_module._log_stream_handler is mock_handler

    def test_handler_start_called_with_title_and_path(self):
        mock_handler = MagicMock()
        mock_handler.start.return_value = "http://1.2.3.4:8998"

        with patch("th_cli.test_run.logging.logger"):
            with patch("th_cli.test_run.log_stream_handler.LogStreamHandler", return_value=mock_handler):
                configure_logger_for_run("test_title", enable_log_streaming=True)

        mock_handler.start.assert_called_once()
        call_kwargs = mock_handler.start.call_args
        assert call_kwargs[1].get("test_run_title") == "test_title" or \
               call_kwargs[0][0] == "test_title"

    def test_returns_path_string_with_streaming_enabled(self):
        mock_handler = MagicMock()
        mock_handler.start.return_value = "http://1.2.3.4:8998"

        with patch("th_cli.test_run.logging.logger"):
            with patch("th_cli.test_run.log_stream_handler.LogStreamHandler", return_value=mock_handler):
                result = configure_logger_for_run("run", enable_log_streaming=True)

        assert isinstance(result, str)

    def test_graceful_fallback_when_handler_start_raises(self):
        mock_handler = MagicMock()
        mock_handler.start.side_effect = RuntimeError("port in use")

        with patch("th_cli.test_run.logging.logger"):
            with patch("th_cli.test_run.log_stream_handler.LogStreamHandler", return_value=mock_handler):
                result = configure_logger_for_run("run", enable_log_streaming=True)

        assert logging_module._log_stream_handler is None
        assert isinstance(result, str)

    def test_graceful_fallback_when_log_stream_handler_import_fails(self):
        """When the LogStreamHandler module import fails inside the function, falls back gracefully."""
        import importlib
        import sys

        # Remove the cached module to force a fresh import attempt inside the function
        original = sys.modules.pop("th_cli.test_run.log_stream_handler", None)
        try:
            sys.modules["th_cli.test_run.log_stream_handler"] = None  # type: ignore[assignment]
            with patch("th_cli.test_run.logging.logger"):
                result = configure_logger_for_run("run", enable_log_streaming=True)
        finally:
            if original is not None:
                sys.modules["th_cli.test_run.log_stream_handler"] = original
            elif "th_cli.test_run.log_stream_handler" in sys.modules:
                del sys.modules["th_cli.test_run.log_stream_handler"]

        assert isinstance(result, str)
        assert logging_module._log_stream_handler is None


# ---------------------------------------------------------------------------
# stop_log_streaming
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStopLogStreaming:
    def setup_method(self):
        _reset_global_handler()

    def test_noop_when_no_handler(self):
        stop_log_streaming()  # must not raise
        assert logging_module._log_stream_handler is None

    def test_calls_stop_on_handler(self):
        mock_handler = MagicMock()
        logging_module._log_stream_handler = mock_handler

        with patch("th_cli.test_run.logging.logger"):
            stop_log_streaming()

        mock_handler.stop.assert_called_once()

    def test_sets_global_to_none_after_stop(self):
        mock_handler = MagicMock()
        logging_module._log_stream_handler = mock_handler

        with patch("th_cli.test_run.logging.logger"):
            stop_log_streaming()

        assert logging_module._log_stream_handler is None

    def test_sets_global_to_none_even_when_stop_raises(self):
        mock_handler = MagicMock()
        mock_handler.stop.side_effect = Exception("already stopped")
        logging_module._log_stream_handler = mock_handler

        with patch("th_cli.test_run.logging.logger"):
            stop_log_streaming()  # must not raise

        assert logging_module._log_stream_handler is None


# ---------------------------------------------------------------------------
# get_log_stream_url
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetLogStreamUrl:
    def setup_method(self):
        _reset_global_handler()

    def test_returns_none_when_no_handler(self):
        result = get_log_stream_url()
        assert result is None

    def test_returns_none_when_handler_not_running(self):
        mock_handler = MagicMock()
        mock_handler.is_running = False
        logging_module._log_stream_handler = mock_handler

        result = get_log_stream_url()
        assert result is None

    def test_returns_url_when_handler_is_running(self):
        mock_handler = MagicMock()
        mock_handler.is_running = True
        mock_handler._get_log_viewer_url.return_value = "http://10.0.0.1:8998"
        logging_module._log_stream_handler = mock_handler

        result = get_log_stream_url()
        assert result == "http://10.0.0.1:8998"

    def test_calls_get_log_viewer_url_on_handler(self):
        mock_handler = MagicMock()
        mock_handler.is_running = True
        mock_handler._get_log_viewer_url.return_value = "http://localhost:8998"
        logging_module._log_stream_handler = mock_handler

        get_log_stream_url()
        mock_handler._get_log_viewer_url.assert_called_once()


# ---------------------------------------------------------------------------
# write_log_file_from_entries
# ---------------------------------------------------------------------------

# 2026-09-21 14:13:20.123456 UTC
_TS = 1790000000.123456


def _entry(message: str, level: str = "INFO", timestamp: float = _TS) -> TestLogRecord:
    return TestLogRecord(level=level, timestamp=timestamp, message=message)


@pytest.mark.unit
class TestWriteLogFileFromEntries:
    @pytest.fixture(autouse=True)
    def log_config(self, tmp_path):
        logging_module._log_file_sink_id = None
        with patch("th_cli.test_run.logging.config") as mock_config:
            mock_config.log_config.output_log_path = str(tmp_path)
            mock_config.log_config.format = "{level: <8} | {time:YYYY-MM-DD HH:mm:ss.SSS Z} | {message}"
            yield mock_config
        logging_module.logger.remove()

    def test_renders_entries_with_configured_format_in_local_time(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TZ", "America/Los_Angeles")
        time.tzset()
        try:
            log_path = tmp_path / "run.log"
            logging_module.write_log_file_from_entries(
                str(log_path), [_entry("first"), _entry("second", level="CHIPTOOL", timestamp=_TS + 1)]
            )
        finally:
            monkeypatch.delenv("TZ")
            time.tzset()

        assert log_path.read_text(encoding="utf-8") == (
            "INFO     | 2026-09-21 07:13:20.123 -07:00 | first\n"
            "CHIPTOOL | 2026-09-21 07:13:21.123 -07:00 | second\n"
        )
        assert not (tmp_path / "run.log.tmp").exists()

    def test_utc_offset_follows_dst_per_entry(self, tmp_path, monkeypatch):
        """Entries either side of a DST change get their own offsets."""
        monkeypatch.setenv("TZ", "America/Los_Angeles")
        time.tzset()
        try:
            log_path = tmp_path / "run.log"
            # 2026-11-01 08:59:59 UTC (PDT) and 09:00:00 UTC (PST)
            logging_module.write_log_file_from_entries(
                str(log_path), [_entry("before", timestamp=1793523599), _entry("after", timestamp=1793523600)]
            )
        finally:
            monkeypatch.delenv("TZ")
            time.tzset()

        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert "01:59:59.000 -07:00" in lines[0]
        assert "01:00:00.000 -08:00" in lines[1]

    def test_messages_are_written_literally(self, tmp_path):
        log_path = tmp_path / "run.log"
        logging_module.write_log_file_from_entries(str(log_path), [_entry("a {brace} and <red>tag</red>")])
        assert log_path.read_text(encoding="utf-8").endswith("| a {brace} and <red>tag</red>\n")

    def test_unknown_level_is_written_under_its_own_name(self, tmp_path):
        log_path = tmp_path / "run.log"
        logging_module.write_log_file_from_entries(str(log_path), [_entry("x", level="SOME_NEW_LEVEL")])
        assert log_path.read_text(encoding="utf-8").startswith("SOME_NEW_LEVEL | ")

    def test_replaces_websocket_file_and_drops_queued_and_later_lines(self, tmp_path):
        """Lines still queued in the enqueue=True file sink must land before the
        replacement, not after it, and nothing logged afterwards reaches the file."""
        log_path = configure_logger_for_run("run")
        logging_module.logger.info("websocket line")

        logging_module.write_log_file_from_entries(log_path, [_entry("backend line")])
        logging_module.logger.info("late line")

        with open(log_path, encoding="utf-8") as f:
            content = f.read()
        assert content.endswith("| backend line\n")
        assert "websocket line" not in content
        assert "late line" not in content
        assert logging_module._log_file_sink_id is None

    def test_replayed_entries_do_not_reach_other_sinks(self, tmp_path):
        seen = []
        logging_module.logger.add(lambda m: seen.append(m.record["message"]), filter=logging_module._is_not_replayed)

        logging_module.write_log_file_from_entries(str(tmp_path / "run.log"), [_entry("backend line")])

        assert seen == []

    def test_failure_keeps_existing_file_and_removes_temp(self, tmp_path):
        log_path = tmp_path / "run.log"
        log_path.write_text("websocket log\n", encoding="utf-8")

        with pytest.raises(ValueError):
            logging_module.write_log_file_from_entries(
                str(log_path), [_entry("ok"), TestLogRecord(level="INFO", timestamp="not a time", message="bad")]
            )

        assert log_path.read_text(encoding="utf-8") == "websocket log\n"
        assert not (tmp_path / "run.log.tmp").exists()
