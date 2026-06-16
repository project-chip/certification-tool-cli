#
# Copyright (c) 2025-2026 Project CHIP Authors
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
"""Unit tests for th_cli/exceptions.py."""

from unittest.mock import MagicMock, patch

import click
import pytest

from th_cli.exceptions import (
    APIError,
    CLIError,
    ConfigurationError,
    handle_api_error,
    handle_file_error,
)
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse


# ---------------------------------------------------------------------------
# CLIError
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCLIError:
    def test_is_click_exception(self):
        err = CLIError("something went wrong")
        assert isinstance(err, click.ClickException)

    def test_message_stored(self):
        err = CLIError("bad stuff")
        assert err.format_message() == "bad stuff"

    def test_default_exit_code_is_1(self):
        err = CLIError("bad stuff")
        assert err.exit_code == 1

    def test_custom_exit_code(self):
        err = CLIError("bad stuff", exit_code=2)
        assert err.exit_code == 2

    def test_show_writes_to_stderr(self):
        err = CLIError("something failed")
        with patch("th_cli.exceptions.click.echo") as mock_echo:
            err.show()
        mock_echo.assert_called_once()
        args, kwargs = mock_echo.call_args
        assert kwargs.get("err") is True

    def test_show_contains_error_message(self):
        err = CLIError("important message")
        captured = []
        with patch("th_cli.exceptions.click.echo", side_effect=lambda msg, **kw: captured.append(msg)):
            err.show()
        assert any("important message" in str(m) for m in captured)


# ---------------------------------------------------------------------------
# APIError
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAPIError:
    def test_is_cli_error(self):
        err = APIError("api failed")
        assert isinstance(err, CLIError)

    def test_message_only(self):
        err = APIError("api failed")
        assert "api failed" in err.format_message()
        assert err.status_code is None
        assert err.content is None

    def test_with_status_code(self):
        err = APIError("not found", status_code=404)
        msg = err.format_message()
        assert "not found" in msg
        assert "404" in msg

    def test_with_content(self):
        err = APIError("server error", content="Internal Server Error")
        msg = err.format_message()
        assert "server error" in msg
        assert "Internal Server Error" in msg

    def test_with_status_code_and_content(self):
        err = APIError("bad request", status_code=400, content="Validation failed")
        msg = err.format_message()
        assert "400" in msg
        assert "Validation failed" in msg

    def test_status_code_none_not_in_message(self):
        err = APIError("plain error", status_code=None)
        msg = err.format_message()
        assert "Status" not in msg

    def test_content_none_not_in_message(self):
        err = APIError("plain error", content=None)
        msg = err.format_message()
        assert " - None" not in msg


# ---------------------------------------------------------------------------
# ConfigurationError
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfigurationError:
    def test_is_cli_error(self):
        err = ConfigurationError("config problem")
        assert isinstance(err, CLIError)

    def test_message_accessible(self):
        err = ConfigurationError("missing hostname")
        assert "missing hostname" in err.format_message()

    def test_default_exit_code(self):
        err = ConfigurationError("missing hostname")
        assert err.exit_code == 1


# ---------------------------------------------------------------------------
# handle_api_error
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleApiError:
    def _make_unexpected_response(self, status_code, content):
        return UnexpectedResponse(status_code=status_code, content=content)

    def test_raises_api_error(self):
        e = self._make_unexpected_response(500, b"server error")
        with pytest.raises(APIError):
            handle_api_error(e, "do something")

    def test_error_message_contains_operation(self):
        e = self._make_unexpected_response(404, b"not found")
        with pytest.raises(APIError) as exc_info:
            handle_api_error(e, "fetch project")
        assert "fetch project" in str(exc_info.value.format_message())

    def test_bytes_content_is_decoded(self):
        e = self._make_unexpected_response(500, b"byte content")
        with pytest.raises(APIError) as exc_info:
            handle_api_error(e, "op")
        err = exc_info.value
        assert isinstance(err.content, str)
        assert "byte content" in err.content

    def test_string_content_passed_through(self):
        e = self._make_unexpected_response(400, "string content")
        with pytest.raises(APIError) as exc_info:
            handle_api_error(e, "op")
        assert exc_info.value.content == "string content"

    def test_none_content(self):
        e = self._make_unexpected_response(503, None)
        with pytest.raises(APIError) as exc_info:
            handle_api_error(e, "op")
        assert exc_info.value.content is None

    def test_status_code_preserved(self):
        e = self._make_unexpected_response(422, b"unprocessable")
        with pytest.raises(APIError) as exc_info:
            handle_api_error(e, "op")
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# handle_file_error
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleFileError:
    def _make_fnf(self, filename, strerror="No such file or directory"):
        err = FileNotFoundError(2, strerror, filename)
        return err

    def test_raises_cli_error(self):
        e = self._make_fnf("/some/file.txt")
        with pytest.raises(CLIError):
            handle_file_error(e)

    def test_error_message_contains_filename(self):
        e = self._make_fnf("/some/file.txt")
        with pytest.raises(CLIError) as exc_info:
            handle_file_error(e)
        assert "/some/file.txt" in exc_info.value.format_message()

    def test_error_message_contains_strerror(self):
        e = self._make_fnf("/some/file.txt", "No such file or directory")
        with pytest.raises(CLIError) as exc_info:
            handle_file_error(e)
        assert "No such file or directory" in exc_info.value.format_message()

    def test_custom_file_type_in_message(self):
        e = self._make_fnf("/config.json")
        with pytest.raises(CLIError) as exc_info:
            handle_file_error(e, file_type="config file")
        # file_type.title() → "Config File"
        assert "Config File" in exc_info.value.format_message()

    def test_default_file_type_is_file(self):
        e = self._make_fnf("/some/path")
        with pytest.raises(CLIError) as exc_info:
            handle_file_error(e)
        # "file" title-cased → "File"
        assert "File" in exc_info.value.format_message()
