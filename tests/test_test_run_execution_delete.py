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
"""Tests for the `test-run-execution delete` command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.test_run_execution import test_run_execution


@pytest.mark.unit
@pytest.mark.cli
class TestDeleteTestRunExecutionCommand:
    """Test cases for the `test-run-execution delete` command."""

    def test_delete_success_with_yes_flag(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test successful deletion with --yes flag skips confirmation."""
        api = mock_sync_apis.test_run_executions_api
        api.remove_test_run_execution_api_v1_test_run_executions__id__delete.return_value = None

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["delete", "--id", "1", "--yes"])

        assert result.exit_code == 0
        assert "Test run execution 1 was deleted." in result.output
        api.remove_test_run_execution_api_v1_test_run_executions__id__delete.assert_called_once_with(id=1)

    def test_delete_success_with_confirmation(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test successful deletion when the user confirms the prompt."""
        api = mock_sync_apis.test_run_executions_api
        api.remove_test_run_execution_api_v1_test_run_executions__id__delete.return_value = None

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["delete", "--id", "1"], input="y\n")

        assert result.exit_code == 0
        assert "Test run execution 1 was deleted." in result.output

    def test_delete_abort_on_no_confirmation(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test deletion is aborted when the user declines confirmation."""
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["delete", "--id", "1"], input="n\n")

        assert result.exit_code == 0  # Aborted, not an error
        assert "Operation cancelled." in result.output
        mock_sync_apis.test_run_executions_api.remove_test_run_execution_api_v1_test_run_executions__id__delete.assert_not_called()  # noqa: E501

    def test_delete_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test that an API error is surfaced to the user."""
        api = mock_sync_apis.test_run_executions_api
        api.remove_test_run_execution_api_v1_test_run_executions__id__delete.side_effect = UnexpectedResponse(
            status_code=404,
            content=b"Not Found",
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["delete", "--id", "1", "--yes"])

        assert result.exit_code == 1
        assert "Error: Failed to delete test run execution ID '1' (Status: 404) - Not Found" in result.output

    def test_delete_requires_id(self, cli_runner: CliRunner) -> None:
        """The --id parameter is required."""
        result = cli_runner.invoke(test_run_execution, ["delete"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--id" in result.output

    def test_delete_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the delete command."""
        result = cli_runner.invoke(test_run_execution, ["delete", "--help"])

        assert result.exit_code == 0
        assert "delete" in result.output
        assert "--id" in result.output
        assert "--yes" in result.output
