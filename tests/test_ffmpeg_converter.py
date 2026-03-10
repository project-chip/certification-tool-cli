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
"""Unit tests for FFmpegStreamConverter and FFmpegNotInstalledError."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

import ffmpeg
import pytest

from th_cli.th_utils.ffmpeg_converter import FFMPEG_NOT_INSTALLED_MSG, FFmpegNotInstalledError, FFmpegStreamConverter

# ---------------------------------------------------------------------------
# FFmpegNotInstalledError
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFFmpegNotInstalledError:
    """Tests for FFmpegNotInstalledError exception class."""

    def test_default_message(self):
        """Default message contains the installation instructions constant."""
        error = FFmpegNotInstalledError()
        assert error.message == FFMPEG_NOT_INSTALLED_MSG
        assert FFMPEG_NOT_INSTALLED_MSG in str(error)

    def test_custom_message(self):
        """Custom message is stored in both .message and str representation."""
        custom = "custom error"
        error = FFmpegNotInstalledError(custom)
        assert error.message == custom
        assert custom in str(error)

    def test_is_runtime_error(self):
        """FFmpegNotInstalledError is a subclass of RuntimeError."""
        assert issubclass(FFmpegNotInstalledError, RuntimeError)


# ---------------------------------------------------------------------------
# FFmpegStreamConverter.check_ffmpeg_installed
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCheckFfmpegInstalled:
    """Tests for FFmpegStreamConverter.check_ffmpeg_installed static method."""

    def test_returns_false_when_ffmpeg_not_in_path(self):
        """Returns (False, message) when shutil.which returns None."""
        with patch("th_cli.th_utils.ffmpeg_converter.shutil.which", return_value=None):
            installed, msg = FFmpegStreamConverter.check_ffmpeg_installed()

        assert installed is False
        assert msg == FFMPEG_NOT_INSTALLED_MSG

    def test_returns_true_when_ffmpeg_found_and_runs(self):
        """Returns (True, '') when ffmpeg is in PATH and runs successfully."""
        with patch("th_cli.th_utils.ffmpeg_converter.shutil.which", return_value="/usr/bin/ffmpeg"):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "ffmpeg version 6.0 Copyright...\nmore info"

            with patch("th_cli.th_utils.ffmpeg_converter.subprocess.run", return_value=mock_result):
                installed, msg = FFmpegStreamConverter.check_ffmpeg_installed()

        assert installed is True
        assert msg == ""

    def test_returns_false_when_ffmpeg_command_fails(self):
        """Returns (False, error) when ffmpeg exits with non-zero return code."""
        with patch("th_cli.th_utils.ffmpeg_converter.shutil.which", return_value="/usr/bin/ffmpeg"):
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""

            with patch("th_cli.th_utils.ffmpeg_converter.subprocess.run", return_value=mock_result):
                installed, msg = FFmpegStreamConverter.check_ffmpeg_installed()

        assert installed is False
        assert "failed to execute" in msg

    def test_returns_false_on_timeout(self):
        """Returns (False, timeout message) when subprocess times out."""
        with patch("th_cli.th_utils.ffmpeg_converter.shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch(
                "th_cli.th_utils.ffmpeg_converter.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=5),
            ):
                installed, msg = FFmpegStreamConverter.check_ffmpeg_installed()

        assert installed is False
        assert "timed out" in msg

    def test_returns_false_on_unexpected_exception(self):
        """Returns (False, error description) for any other exception."""
        with patch("th_cli.th_utils.ffmpeg_converter.shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch(
                "th_cli.th_utils.ffmpeg_converter.subprocess.run",
                side_effect=OSError("Permission denied"),
            ):
                installed, msg = FFmpegStreamConverter.check_ffmpeg_installed()

        assert installed is False
        assert "Error checking FFmpeg" in msg


# ---------------------------------------------------------------------------
# FFmpegStreamConverter.start_conversion
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStartConversion:
    """Tests for FFmpegStreamConverter.start_conversion."""

    def test_raises_when_ffmpeg_not_installed(self):
        """start_conversion raises FFmpegNotInstalledError if ffmpeg is absent."""
        converter = FFmpegStreamConverter()

        with patch.object(
            FFmpegStreamConverter,
            "check_ffmpeg_installed",
            return_value=(False, FFMPEG_NOT_INSTALLED_MSG),
        ):
            with pytest.raises(FFmpegNotInstalledError):
                converter.start_conversion()

    def test_returns_false_on_ffmpeg_error(self):
        """start_conversion returns False when ffmpeg-python raises ffmpeg.Error."""
        converter = FFmpegStreamConverter()

        with patch.object(FFmpegStreamConverter, "check_ffmpeg_installed", return_value=(True, "")):
            with patch("th_cli.th_utils.ffmpeg_converter.ffmpeg.run_async", side_effect=ffmpeg.Error("err", "", b"")):
                result = converter.start_conversion()

        assert result is False

    def test_returns_false_on_unexpected_error(self):
        """start_conversion returns False on any unexpected exception."""
        converter = FFmpegStreamConverter()

        with patch.object(FFmpegStreamConverter, "check_ffmpeg_installed", return_value=(True, "")):
            with patch(
                "th_cli.th_utils.ffmpeg_converter.ffmpeg.run_async",
                side_effect=RuntimeError("unexpected"),
            ):
                result = converter.start_conversion()

        assert result is False


# ---------------------------------------------------------------------------
# FFmpegStreamConverter.feed_data / get_converted_data / stop
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFeedDataAndGetConvertedData:
    """Tests for feed_data, get_converted_data, and stop methods."""

    def test_feed_data_writes_to_process_stdin(self):
        """feed_data writes bytes to ffmpeg_process.stdin."""
        converter = FFmpegStreamConverter()
        mock_process = MagicMock()
        converter.ffmpeg_process = mock_process

        converter.feed_data(b"\x00\x01\x02")

        mock_process.stdin.write.assert_called_once_with(b"\x00\x01\x02")
        mock_process.stdin.flush.assert_called_once()

    def test_feed_data_does_nothing_when_no_process(self):
        """feed_data silently skips when ffmpeg_process is None."""
        converter = FFmpegStreamConverter()
        converter.ffmpeg_process = None

        # Should not raise
        converter.feed_data(b"\x00\x01\x02")

    def test_feed_data_handles_write_error_gracefully(self):
        """feed_data logs error and does not propagate exceptions."""
        converter = FFmpegStreamConverter()
        mock_process = MagicMock()
        mock_process.stdin.write.side_effect = OSError("broken pipe")
        converter.ffmpeg_process = mock_process

        # Should not raise
        converter.feed_data(b"\xde\xad\xbe\xef")

    def test_get_converted_data_returns_queued_item(self):
        """get_converted_data returns item from output_queue."""
        converter = FFmpegStreamConverter()
        converter.output_queue.put_nowait(b"mp4data")

        result = converter.get_converted_data(timeout=0.1)

        assert result == b"mp4data"

    def test_get_converted_data_returns_none_on_empty_queue(self):
        """get_converted_data returns None when queue is empty after timeout."""
        converter = FFmpegStreamConverter()

        result = converter.get_converted_data(timeout=0.05)

        assert result is None

    def test_stop_terminates_process(self):
        """stop calls terminate/wait on the ffmpeg process."""
        converter = FFmpegStreamConverter()
        mock_process = MagicMock()
        converter.ffmpeg_process = mock_process

        converter.stop()

        mock_process.stdin.close.assert_called_once()
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert converter.ffmpeg_process is None

    def test_stop_does_nothing_when_no_process(self):
        """stop silently handles the case where ffmpeg_process is None."""
        converter = FFmpegStreamConverter()
        converter.ffmpeg_process = None

        # Should not raise
        converter.stop()

    def test_stop_handles_exception_gracefully(self):
        """stop logs error and clears ffmpeg_process even when terminate raises."""
        converter = FFmpegStreamConverter()
        mock_process = MagicMock()
        mock_process.terminate.side_effect = OSError("already dead")
        converter.ffmpeg_process = mock_process

        # Should not raise
        converter.stop()

        assert converter.ffmpeg_process is None
