#
# Copyright (c) 2025 Project CHIP Authors
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
"""Tests for the abort_testing command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from httpx import Headers

from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.abort_testing import abort_testing
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestAbortTestingCommand:
    """Test cases for the abort_testing command."""

    def test_abort_testing_success(self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_api_client: Mock) -> None:
        """Test successful abort testing operation."""
        # Arrange
        expected_response = {"detail": "Testing aborted successfully"}
        api = mock_sync_apis.test_run_executions_api.abort_testing_api_v1_test_run_executions_abort_testing_post
        api.return_value = expected_response

        with patch("th_cli.commands.abort_testing.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.abort_testing.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 0
        assert "Testing aborted successfully" in result.output
        api.assert_called_once()
        mock_api_client.close.assert_called_once()

    def test_abort_testing_success_default_message(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test abort testing with default message when no detail is provided."""
        # Arrange
        expected_response = {}
        api = mock_sync_apis.test_run_executions_api.abort_testing_api_v1_test_run_executions_abort_testing_post

        api.return_value = expected_response
        with patch("th_cli.commands.abort_testing.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 0
        assert "Testing aborted" in result.output
        api.assert_called_once()

    def test_abort_testing_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test abort testing with configuration error."""
        # Arrange
        with patch(
            "th_cli.commands.abort_testing.get_client",
            side_effect=ConfigurationError("Could not connect to server")
        ):
            # Act
            result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_abort_testing_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_api_client: Mock) -> None:
        """Test abort testing with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=404,
            reason_phrase="Not Found",
            content=b"Not Found",
            headers=Headers(),
        )
        api = mock_sync_apis.test_run_executions_api.abort_testing_api_v1_test_run_executions_abort_testing_post

        api.side_effect = api_exception
        with patch("th_cli.commands.abort_testing.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.abort_testing.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to abort testing (Status: 404) - Not Found" in result.output
        mock_api_client.close.assert_called_once()

    def test_abort_testing_generic_exception(
            self,
            cli_runner: CliRunner,
            mock_sync_apis: Mock,
            mock_api_client: Mock
    ) -> None:
        """Test abort testing with generic exception."""
        # Arrange
        api = mock_sync_apis.test_run_executions_api.abort_testing_api_v1_test_run_executions_abort_testing_post

        api.side_effect = Exception("Unexpected error")
        with patch("th_cli.commands.abort_testing.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.abort_testing.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 1
        assert "Unexpected error" in str(result.exception)
        mock_api_client.close.assert_called_once()

    def test_abort_testing_client_cleanup_on_exception(self, cli_runner: CliRunner, mock_api_client: Mock) -> None:
        """Test that client is properly cleaned up even when an exception occurs."""
        # Arrange
        with patch("th_cli.commands.abort_testing.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.abort_testing.SyncApis", side_effect=Exception("API creation failed")):
                # Act
                result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 1
        mock_api_client.close.assert_called_once()

    def test_abort_testing_no_client_cleanup_when_client_is_none(self, cli_runner: CliRunner) -> None:
        """Test behavior when client is None and cleanup should not fail."""
        # Arrange
        with patch("th_cli.commands.abort_testing.get_client", side_effect=ConfigurationError("Connection failed")):
            # Act
            result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 1
        # No assertion on client.close() since client is None

    def test_abort_testing_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for abort_testing command."""
        # Act
        result = cli_runner.invoke(abort_testing, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "Abort the current test run execution" in result.output

    @pytest.mark.parametrize("response_data", [
        {"detail": "Test execution aborted"},
        {"detail": "No active test execution"},
        {"detail": "Test Engine is not active."},
        {"message": "Operation completed"},
        {},
    ])
    def test_abort_testing_various_response_formats(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        response_data: dict,
    ) -> None:
        """Test abort testing with various response formats."""
        # Arrange
        api = mock_sync_apis.test_run_executions_api.abort_testing_api_v1_test_run_executions_abort_testing_post

        api.return_value = response_data
        with patch("th_cli.commands.abort_testing.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 0
        # Should contain either the detail message or the default message
        if response_data and "detail" in response_data:
            assert response_data["detail"] in result.output
        else:
            assert "Testing aborted" in result.output

    @pytest.mark.parametrize("status_code,content", [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (500, "Internal Server Error"),
        (503, "Service Unavailable")
    ])
    def test_abort_testing_various_api_errors(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        status_code: int,
        content: str
    ) -> None:
        """Test abort testing with various API error status codes."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=status_code,
            reason_phrase=content,
            content=content.encode('utf-8'),
            headers=Headers(),
        )
        api = mock_sync_apis.test_run_executions_api.abort_testing_api_v1_test_run_executions_abort_testing_post

        api.side_effect = api_exception
        with patch("th_cli.commands.abort_testing.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(abort_testing)

        # Assert
        assert result.exit_code == 1
        assert f"Failed to abort testing (Status: {status_code})" in result.output
        assert content in result.output
