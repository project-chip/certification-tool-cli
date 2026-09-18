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
"""Tests for the `test-run-execution archive` and `test-run-execution unarchive` commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.test_run_execution import test_run_execution


@pytest.mark.unit
@pytest.mark.cli
class TestArchiveTestRunExecutionCommand:
    """Test cases for the `test-run-execution archive` command."""

    def test_archive_success(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test successful archiving."""
        api = mock_sync_apis.test_run_executions_api
        api.archive_api_v1_test_run_executions__id__archive_post.return_value = None

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["archive", "--id", "1"])

        assert result.exit_code == 0
        assert "Test run execution 1 was archived." in result.output
        api.archive_api_v1_test_run_executions__id__archive_post.assert_called_once_with(id=1)

    def test_archive_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test that an API error is surfaced to the user."""
        api = mock_sync_apis.test_run_executions_api
        api.archive_api_v1_test_run_executions__id__archive_post.side_effect = UnexpectedResponse(
            status_code=404,
            content=b"Not Found",
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["archive", "--id", "1"])

        assert result.exit_code == 1
        assert "Error: Failed to archive test run execution ID '1' (Status: 404) - Not Found" in result.output

    def test_archive_requires_id(self, cli_runner: CliRunner) -> None:
        """The --id parameter is required."""
        result = cli_runner.invoke(test_run_execution, ["archive"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--id" in result.output

    def test_archive_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the archive command."""
        result = cli_runner.invoke(test_run_execution, ["archive", "--help"])

        assert result.exit_code == 0
        assert "archive" in result.output
        assert "--id" in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestUnarchiveTestRunExecutionCommand:
    """Test cases for the `test-run-execution unarchive` command."""

    def test_unarchive_success(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test successful unarchiving."""
        api = mock_sync_apis.test_run_executions_api
        api.unarchive_api_v1_test_run_executions__id__unarchive_post.return_value = None

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["unarchive", "--id", "1"])

        assert result.exit_code == 0
        assert "Test run execution 1 was unarchived." in result.output
        api.unarchive_api_v1_test_run_executions__id__unarchive_post.assert_called_once_with(id=1)

    def test_unarchive_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """Test that an API error is surfaced to the user."""
        api = mock_sync_apis.test_run_executions_api
        api.unarchive_api_v1_test_run_executions__id__unarchive_post.side_effect = UnexpectedResponse(
            status_code=404,
            content=b"Not Found",
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["unarchive", "--id", "1"])

        assert result.exit_code == 1
        assert "Error: Failed to unarchive test run execution ID '1' (Status: 404) - Not Found" in result.output

    def test_unarchive_requires_id(self, cli_runner: CliRunner) -> None:
        """The --id parameter is required."""
        result = cli_runner.invoke(test_run_execution, ["unarchive"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--id" in result.output

    def test_unarchive_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the unarchive command."""
        result = cli_runner.invoke(test_run_execution, ["unarchive", "--help"])

        assert result.exit_code == 0
        assert "unarchive" in result.output
        assert "--id" in result.output
