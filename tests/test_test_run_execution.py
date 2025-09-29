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
"""Tests for the test_run_execution command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from httpx import Headers

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.test_run_execution import test_run_execution
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestTestRunExecutionCommand:
    """Test cases for the test_run_execution command."""

    def test_test_run_execution_success_all(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock
    ) -> None:
        """Test successful test run execution history retrieval (all executions)."""
        # Arrange
        test_executions = [
            api_models.TestRunExecution(
                id=1,
                title="Test Run 1",
                state=api_models.TestStateEnum.PASSED,
                project_id=1
            ),
            api_models.TestRunExecution(
                id=2,
                title="Test Run 2",
                state=api_models.TestStateEnum.FAILED,
                project_id=1,
            )
        ]
        api = mock_sync_apis.test_run_executions_api.read_test_run_executions_api_v1_test_run_executions_get

        api.return_value = test_executions
        with patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(test_run_execution)

        # Assert
        assert result.exit_code == 0
        assert "ID" in result.output
        assert "Title" in result.output
        assert "State" in result.output
        assert "Error" in result.output
        assert "Test Run 1" in result.output
        assert "Test Run 2" in result.output
        assert "PASSED" in result.output
        assert "FAILED" in result.output
        api.assert_called_once_with(skip=None, limit=None)
        mock_api_client.close.assert_called_once()

    def test_test_run_execution_success_specific_id(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test run execution history retrieval for specific ID."""
        # Arrange
        test_execution = api_models.TestRunExecution(
            id=1,
            title="Specific Test Run",
            state=api_models.TestStateEnum.EXECUTING,
            project_id=1
        )
        api = mock_sync_apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions_id_get

        api.return_value = test_execution
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert "Specific Test Run" in result.output
        assert "EXECUTING" in result.output
        api.assert_called_once_with(id=1)

    def test_test_run_execution_success_with_pagination(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test run execution history retrieval with pagination."""
        # Arrange
        test_executions = [
            api_models.TestRunExecution(
                id=3,
                title="Test Run 3",
                state=api_models.TestStateEnum.PENDING,
                project_id=1
            )
        ]
        api = mock_sync_apis.test_run_executions_api.read_test_run_executions_api_v1_test_run_executions_get

        api.return_value = test_executions
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--skip", "10", "--limit", "5"])

        # Assert
        assert result.exit_code == 0
        assert "Test Run 3" in result.output
        api.assert_called_once_with(skip=10, limit=5)

    def test_test_run_execution_success_json_output(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test run execution history retrieval with JSON output."""
        # Arrange
        test_execution = api_models.TestRunExecution(
            id=1,
            title="JSON Test Run",
            state=api_models.TestStateEnum.PASSED,
            project_id=1
        )
        api = mock_sync_apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions_id_get

        api.return_value = test_execution
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "1", "--json"])

        # Assert
        assert result.exit_code == 0
        # Should contain JSON formatted output
        assert '"id":' in result.output
        assert '"title":' in result.output
        assert '"state":' in result.output
        # Should not contain table headers
        assert "ID" not in result.output or '"ID"' in result.output

    def test_test_run_execution_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test test run execution history with configuration error."""
        # Arrange
        with patch("th_cli.commands.test_run_execution.get_client",
                   side_effect=ConfigurationError("Could not connect to server")):
            # Act
            result = cli_runner.invoke(test_run_execution)

        # Assert
        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_test_run_execution_api_error_by_id(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock
    ) -> None:
        """Test test run execution history with API error when fetching by ID."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=404,
            reason_phrase="Not Found",
            content=b"Not Found",
            headers=Headers(),
        )
        api = mock_sync_apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions_id_get

        api.side_effect = api_exception
        with patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(test_run_execution, ["--id", "999"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to get test run execution (Status: 404) - Not Found" in result.output
        mock_api_client.close.assert_called_once()

    def test_test_run_execution_api_error_batch(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test test run execution history with API error when fetching batch."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=500,
            reason_phrase="Internal Server Error",
            content=b"Internal Server Error",
            headers=Headers(),
        )
        api = mock_sync_apis.test_run_executions_api.read_test_run_executions_api_v1_test_run_executions_get

        api.side_effect = api_exception
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution)

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to get test run executions (Status: 500) - Internal Server Error" in result.output

    def test_test_run_execution_client_cleanup_on_exception(
            self,
            cli_runner: CliRunner,
            mock_api_client: Mock
    ) -> None:
        """Test that client is properly cleaned up even when an exception occurs."""
        # Arrange
        with patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.test_run_execution.SyncApis",
                       side_effect=Exception("API creation failed")):
                # Act
                result = cli_runner.invoke(test_run_execution)

        # Assert
        assert result.exit_code == 1
        mock_api_client.close.assert_called_once()

    def test_test_run_execution_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for test_run_execution command."""
        # Act
        result = cli_runner.invoke(test_run_execution, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "List test run execution history" in result.output
        assert "--id" in result.output
        assert "--skip" in result.output
        assert "--limit" in result.output
        assert "--json" in result.output

    @pytest.mark.parametrize("state,expected_display", [
        (api_models.TestStateEnum.PENDING, "PENDING"),
        (api_models.TestStateEnum.EXECUTING, "EXECUTING"),
        (api_models.TestStateEnum.PASSED, "PASSED"),
        (api_models.TestStateEnum.FAILED, "FAILED"),
        (api_models.TestStateEnum.ERROR, "ERROR"),
        (api_models.TestStateEnum.CANCELLED, "CANCELLED"),
        (api_models.TestStateEnum.NOT_APPLICABLE, "NOT_APPLICABLE"),
    ])
    def test_test_run_execution_various_states(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        state: api_models.TestStateEnum,
        expected_display: str
    ) -> None:
        """Test test run execution history with various execution states."""
        # Arrange
        test_execution = api_models.TestRunExecution(
            id=1,
            title="State Test Run",
            state=state,
            project_id=1
        )
        api = mock_sync_apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions_id_get

        api.return_value = test_execution
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert expected_display in result.output

    def test_test_run_execution_table_output_format(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test that table output is properly formatted."""
        # Arrange
        test_executions = [
            api_models.TestRunExecution(
                id=1,
                title="Long Test Run Title That Should Be Formatted Properly",
                state=api_models.TestStateEnum.PASSED,
                project_id=1,
                error="No Error"
            ),
            api_models.TestRunExecution(
                id=2,
                title="Short Title",
                state=api_models.TestStateEnum.FAILED,
                project_id=1,
                error="Some error occurred"
            )
        ]
        api = mock_sync_apis.test_run_executions_api.read_test_run_executions_api_v1_test_run_executions_get

        api.return_value = test_executions
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution)

        # Assert
        assert result.exit_code == 0
        # Check for proper table formatting
        lines = result.output.strip().split('\n')
        # Should have header line and at least two data lines
        assert len(lines) >= 3
        # Header should be present
        assert any("ID" in line and "Title" in line for line in lines)
        # Both test executions should be present
        assert any("Long Test Run Title" in line for line in lines)
        assert any("Short Title" in line for line in lines)

    @pytest.mark.parametrize("skip,limit", [
        (None, None),
        (0, 10),
        (5, 20),
        (100, 1),
    ])
    def test_test_run_execution_pagination_parameters(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        skip: int,
        limit: int
    ) -> None:
        """Test test run execution history with various pagination parameters."""
        # Arrange
        test_executions = [
            api_models.TestRunExecution(
                id=1,
                title="Paginated Test Run",
                state=api_models.TestStateEnum.PASSED,
                project_id=1
            )
        ]
        api = mock_sync_apis.test_run_executions_api.read_test_run_executions_api_v1_test_run_executions_get

        api.return_value = test_executions
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            args = []
            if skip is not None:
                args.extend(["--skip", str(skip)])
            if limit is not None:
                args.extend(["--limit", str(limit)])
            result = cli_runner.invoke(test_run_execution, args)

        # Assert
        assert result.exit_code == 0
        api.assert_called_once_with(skip=skip, limit=limit)

    def test_test_run_execution_error_display(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test that error information is properly displayed."""
        # Arrange
        test_execution = api_models.TestRunExecution(
            id=1,
            title="Failed Test Run",
            state=api_models.TestStateEnum.ERROR,
            project_id=1,
            error="Test execution failed due to network timeout"
        )
        api = mock_sync_apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions_id_get

        api.return_value = test_execution
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert "Test execution failed due to network timeout" in str(result.output)

    def test_test_run_execution_no_error_display(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test that 'No Error' is displayed when error is None."""
        # Arrange
        test_execution = api_models.TestRunExecution(
            id=1,
            title="Successful Test Run",
            state=api_models.TestStateEnum.PASSED,
            project_id=1,
            error=None
        )
        api = mock_sync_apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions_id_get

        api.return_value = test_execution
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert "No Error" in str(result.output)

    @pytest.mark.parametrize("json_flag", [True, False])
    def test_test_run_execution_output_modes(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        json_flag: bool
    ) -> None:
        """Test test run execution history with both table and JSON output modes."""
        # Arrange
        test_executions = [
            api_models.TestRunExecution(
                id=1,
                title="Output Mode Test",
                state=api_models.TestStateEnum.PASSED,
                project_id=1
            )
        ]
        api = mock_sync_apis.test_run_executions_api.read_test_run_executions_api_v1_test_run_executions_get

        api.return_value = test_executions
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            args = ["--json"] if json_flag else []
            result = cli_runner.invoke(test_run_execution, args)

        # Assert
        assert result.exit_code == 0
        if json_flag:
            # JSON output should have quotes around keys
            assert '"id":' in result.output
            assert '"title":' in result.output
            assert "ID" not in result.output or '"ID"' in result.output
        else:
            # Table output should have formatted headers
            assert "ID" in result.output
            assert "Title" in result.output
            assert '"id":' not in result.output

    def test_test_run_execution_log_success_with_content(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test run execution log retrieval with log content."""
        # Arrange
        log_content = """
            2025-01-01 10:00:01 [INFO] Starting test execution
            2025-01-01 10:00:02 [INFO] Initializing test environment
            2025-01-01 10:00:03 [DEBUG] Loading test configuration
            2025-01-01 10:00:04 [INFO] Running test TC-ACE-1.1
            2025-01-01 10:00:10 [INFO] Test TC-ACE-1.1 passed
            2025-01-01 10:00:11 [INFO] Test execution completed successfully
        """.strip()

        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 0
        assert "Starting test execution" in result.output
        assert "Test TC-ACE-1.1 passed" in result.output
        assert "Test execution completed successfully" in result.output
        api.assert_called_once_with(id=123, json_entries=False, download=False)

    def test_test_run_execution_log_success_no_content(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test run execution log retrieval with no log content."""
        # Arrange
        mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get.return_value = None

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 0
        assert "No log content available for this test run execution." in result.output

    def test_test_run_execution_log_success_empty_content(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful test run execution log retrieval with empty log content."""
        # Arrange
        mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get.return_value = ""

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 0
        assert "No log content available for this test run execution." in result.output

    def test_test_run_execution_log_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test test run execution log with configuration error."""
        # Arrange
        with patch("th_cli.commands.test_run_execution.get_client",
                   side_effect=ConfigurationError("Could not connect to server")):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_test_run_execution_log_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test test run execution log with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=404,
            reason_phrase="Test run execution not found",
            content=b"Test run execution not found",
            headers=Headers(),
        )
        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.side_effect = api_exception
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "999", "--log"])

        # Assert
        error_text = "Error: Failed to fetch test run execution log (Status: 404) - Test run execution not found"
        assert result.exit_code == 1
        assert error_text in result.output

    def test_test_run_execution_log_required_id_parameter(self, cli_runner: CliRunner) -> None:
        """Test that the --id parameter is required."""
        # Act
        result = cli_runner.invoke(test_run_execution, ["--log"])

        # Assert
        assert result.exit_code != 0
        assert "Missing option" in result.output or "Error" in result.output

    def test_test_run_execution_log_multiline_content(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test test run execution log with multiline log content."""
        # Arrange
        log_content = """
            Line 1: Test started
            Line 2: Configuration loaded
            Line 3:
            Line 4: Empty line above
            Line 5: Test completed with success
            Line 6: Final summary:
            - Total tests: 5
            - Passed: 5
            - Failed: 0
        """

        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "456", "--log"])

        # Assert
        assert result.exit_code == 0
        assert "Line 1: Test started" in result.output
        assert "Line 5: Test completed with success" in result.output
        assert "Total tests: 5" in result.output
        assert "Passed: 5" in result.output

    def test_test_run_execution_log_special_characters(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test test run execution log with special characters in content."""
        # Arrange
        log_content = """Log with special chars: !@#$%^&*()
Unicode content: 测试内容 αβγδ
JSON-like content: {"status": "success", "count": 42}
XML-like content: <test result="passed">TC-ACE-1.1</test>
Escape sequences: \n\t\r"""

        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "789", "--log"])

        # Assert
        assert result.exit_code == 0
        assert "!@#$%^&*()" in result.output
        assert '"status": "success"' in result.output
        assert "<test result=" in result.output

    def test_test_run_execution_log_large_content(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test test run execution log with large log content."""
        # Arrange
        # Simulate a large log file
        log_lines = [f"Log line {i}: Some test execution details" for i in range(1000)]
        log_content = "\n".join(log_lines)

        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "1000", "--log"])

        # Assert
        assert result.exit_code == 0
        assert "Log line 1:" in result.output
        assert "Log line 999:" in result.output
        # Verify that we can handle large content without truncation
        assert len(result.output.split('\n')) >= 1000

    @pytest.mark.parametrize("test_id", ["1", "123", "999", "12345"])
    def test_test_run_execution_log_various_ids(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        test_id: str
    ) -> None:
        """Test test run execution log with various ID values."""
        # Arrange
        log_content = f"Log for test run execution ID: {test_id}"
        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", test_id, "--log"])

        # Assert
        assert result.exit_code == 0
        assert f"Log for test run execution ID: {test_id}" in result.output
        api.assert_called_once_with(
            id=int(test_id), json_entries=False, download=False
        )

    @pytest.mark.parametrize("status_code,content", [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Test run execution not found"),
        (500, "Internal Server Error"),
        (503, "Service Unavailable")
    ])
    def test_test_run_execution_log_various_api_errors(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        status_code: int,
        content: str
    ) -> None:
        """Test test run execution log with various API error status codes."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=status_code,
            reason_phrase=content,
            content=content.encode('utf-8'),
            headers=Headers(),
        )
        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.side_effect = api_exception
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 1
        assert f"Failed to fetch test run execution log (Status: {status_code})" in result.output
        assert content in result.output

    def test_test_run_execution_log_client_context_manager(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock
    ) -> None:
        """Test that client is properly managed using context manager."""
        # Arrange
        log_content = "Test log content"
        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 0
        # The command uses context manager, so close should be called automatically
        mock_api_client.close.assert_called_once()

    def test_test_run_execution_log_api_parameters(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test that the correct API parameters are passed."""
        # Arrange
        log_content = "Test log content"
        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "42", "--log"])

        # Assert
        assert result.exit_code == 0
        # Verify the API is called with correct parameters
        api.assert_called_once_with(
            id=42, json_entries=False, download=False
        )

    def test_test_run_execution_log_whitespace_content(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test test run execution log with whitespace-only content."""
        # Arrange
        log_content = "   \n\t  \n   "
        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.return_value = log_content
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 0
        # Should still output the whitespace content as-is
        assert result.output.strip() == log_content.rstrip()

    def test_test_run_execution_log_generic_exception(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test test run execution log with generic exception."""
        # Arrange
        api = mock_sync_apis.test_run_executions_api.download_log_api_v1_test_run_executions_id_log_get

        api.side_effect = Exception("Network timeout")
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(test_run_execution, ["--id", "123", "--log"])

        # Assert
        assert result.exit_code == 1
        assert "Network timeout" in str(result.exception)
