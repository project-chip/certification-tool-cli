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
"""Tests for the `test-run-execution rename` command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.test_run_execution import test_run_execution


@pytest.mark.unit
@pytest.mark.cli
class TestRenameTestRunExecutionCommand:
    """Test cases for the `test-run-execution rename` command."""

    def test_rename_success(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test successful rename."""
        api = mock_sync_apis.test_run_executions_api
        api.rename_test_run_execution_api_v1_test_run_executions__id__rename_put.return_value = (
            api_models.TestRunExecutionWithChildren(id=1, title="New Name", state=api_models.TestStateEnum.pending)
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["rename", "--id", "1", "--name", "New Name"])

        assert result.exit_code == 0
        assert "Test run execution 1 was renamed to 'New Name'." in result.output
        api.rename_test_run_execution_api_v1_test_run_executions__id__rename_put.assert_called_once_with(
            id=1, new_execution_name="New Name"
        )

    def test_rename_echoes_stripped_title_from_response(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """The backend strips whitespace from new_execution_name before persisting; the
        success message must echo the response's title, not the raw --name input, so it
        reflects what was actually saved."""
        api = mock_sync_apis.test_run_executions_api
        api.rename_test_run_execution_api_v1_test_run_executions__id__rename_put.return_value = (
            api_models.TestRunExecutionWithChildren(id=1, title="New Name", state=api_models.TestStateEnum.pending)
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["rename", "--id", "1", "--name", "  New Name  "])

        assert result.exit_code == 0
        assert "Test run execution 1 was renamed to 'New Name'." in result.output
        assert "'  New Name  '" not in result.output

    def test_rename_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test that an API error is surfaced to the user."""
        api = mock_sync_apis.test_run_executions_api
        api.rename_test_run_execution_api_v1_test_run_executions__id__rename_put.side_effect = UnexpectedResponse(
            status_code=404,
            content=b"Not Found",
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["rename", "--id", "1", "--name", "New Name"])

        assert result.exit_code == 1
        assert "Error: Failed to rename test run execution ID '1' (Status: 404) - Not Found" in result.output

    def test_rename_requires_id(self, cli_runner: CliRunner) -> None:
        """The --id parameter is required."""
        result = cli_runner.invoke(test_run_execution, ["rename", "--name", "New Name"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--id" in result.output

    def test_rename_requires_name(self, cli_runner: CliRunner) -> None:
        """The --name parameter is required."""
        result = cli_runner.invoke(test_run_execution, ["rename", "--id", "1"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--name" in result.output

    def test_rename_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the rename command."""
        result = cli_runner.invoke(test_run_execution, ["rename", "--help"])

        assert result.exit_code == 0
        assert "rename" in result.output
        assert "--id" in result.output
        assert "--name" in result.output
