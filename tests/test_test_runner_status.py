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
"""Tests for the test_runner_status command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen import models as api_models
from th_cli.commands.test_runner_status import test_runner_status
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestTestRunnerStatusCommand:
    """Test cases for the test_runner_status command."""

    def test_test_runner_status_success_idle(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock
    ) -> None:
        """Test successful test runner status retrieval when idle."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=api_models.TestRunnerState.IDLE,
            test_run_execution_id=None
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 0
        assert "Matter Test Runner Status" in result.output
        assert "State: IDLE" in result.output
        assert "No active test run" in result.output
        api.assert_called_once()
        mock_api_client.close.assert_called_once()

    def test_test_runner_status_success_running(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test runner status retrieval when running."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=api_models.TestRunnerState.RUNNING,
            test_run_execution_id=123
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 0
        assert "Matter Test Runner Status" in result.output
        assert "State: RUNNING" in result.output
        assert "Active Test Run ID: 123" in result.output
        assert "No active test run" not in result.output

    def test_test_runner_status_success_json_output(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test runner status retrieval with JSON output."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=api_models.TestRunnerState.READY,
            test_run_execution_id=None
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_runner_status, ["--json"])

        # Assert
        assert result.exit_code == 0
        # Should contain JSON formatted output
        assert '"state":' in result.output
        assert '"test_run_execution_id":' in result.output
        # Should not contain the formatted table output
        assert "Matter Test Runner Status" not in result.output

    def test_test_runner_status_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test test runner status with configuration error."""
        # Arrange
        with patch(
            "th_cli.commands.test_runner_status.get_client",
            side_effect=ConfigurationError("Could not connect to server")
        ):
            # Act
            result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_test_runner_status_generic_exception(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock
    ) -> None:
        """Test test runner status with generic exception."""
        # Arrange
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.side_effect = Exception("Network error")
        with patch("th_cli.commands.test_runner_status.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 1
        assert "Network error" in str(result)
        mock_api_client.close.assert_called_once()

    def test_test_runner_status_client_cleanup_on_exception(self, cli_runner: CliRunner, mock_api_client: Mock) -> None:
        """Test that client is properly cleaned up even when an exception occurs."""
        # Arrange
        with patch("th_cli.commands.test_runner_status.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.test_runner_status.SyncApis", side_effect=Exception("API creation failed")):
                # Act
                result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 1
        mock_api_client.close.assert_called_once()

    def test_test_runner_status_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for test_runner_status command."""
        # Act
        result = cli_runner.invoke(test_runner_status, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "Get the current test runner" in result.output
        assert "--json" in result.output
        assert "Print JSON response for more details" in result.output

    @pytest.mark.parametrize("state,execution_id,expected_state", [
        (api_models.TestRunnerState.IDLE, None, "IDLE"),
        (api_models.TestRunnerState.LOADING, None, "LOADING"),
        (api_models.TestRunnerState.READY, None, "READY"),
        (api_models.TestRunnerState.RUNNING, 456, "RUNNING"),
    ])
    def test_test_runner_status_various_states(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        state: api_models.TestRunnerState,
        execution_id: int,
        expected_state: str
    ) -> None:
        """Test test runner status with various states."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=state,
            test_run_execution_id=execution_id
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 0
        assert f"State: {expected_state}" in result.output
        if execution_id:
            assert f"Active Test Run ID: {execution_id}" in result.output
        else:
            assert "No active test run" in result.output

    def test_test_runner_status_output_format_consistency(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test that output format is consistent and well-formatted."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=api_models.TestRunnerState.RUNNING,
            test_run_execution_id=789
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 0
        # Check for proper formatting structure
        lines = result.output.strip().split('\n')
        # Should have empty line, header, state line, and execution id line
        assert len(lines) >= 3
        assert any("Matter Test Runner Status" in line for line in lines)
        assert any("State:" in line for line in lines)
        assert any("Active Test Run ID:" in line for line in lines)

    @pytest.mark.parametrize("json_flag", [True, False])
    def test_test_runner_status_output_modes(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        json_flag: bool
    ) -> None:
        """Test test runner status with both table and JSON output modes."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=api_models.TestRunnerState.IDLE,
            test_run_execution_id=None
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
            # Act
            args = ["--json"] if json_flag else []
            result = cli_runner.invoke(test_runner_status, args)

        # Assert
        assert result.exit_code == 0
        if json_flag:
            # JSON output should have quotes around keys
            assert '"state":' in result.output
            assert '"test_run_execution_id":' in result.output
            assert "Matter Test Runner Status" not in result.output
        else:
            # Table output should have formatted headers
            assert "Matter Test Runner Status" in result.output
            assert "State:" in result.output
            assert '"state":' not in result.output

    def test_test_runner_status_state_display_formatting(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test that state is properly formatted with colorization."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=api_models.TestRunnerState.RUNNING,
            test_run_execution_id=999
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 0
        # The state should be displayed with proper formatting
        # Note: Colors are disabled in tests, so we just check for the state value
        assert "RUNNING" in result.output

    def test_test_runner_status_no_active_test_run_message(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test the 'No active test run' message is displayed correctly."""
        # Arrange
        status = api_models.TestRunnerStatus(
            state=api_models.TestRunnerState.READY,
            test_run_execution_id=None
        )
        api = mock_sync_apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get

        api.return_value = status
        with patch("th_cli.commands.test_runner_status.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_runner_status)

        # Assert
        assert result.exit_code == 0
        assert "No active test run" in result.output
        assert "Active Test Run ID:" not in result.output
