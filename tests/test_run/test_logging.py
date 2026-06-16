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

from unittest.mock import MagicMock, call, patch

import pytest

import th_cli.test_run.logging as logging_module
from th_cli.test_run.logging import (
    configure_logger_for_run,
    get_log_stream_url,
    stop_log_streaming,
)


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
