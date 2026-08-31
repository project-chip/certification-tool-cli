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
"""Tests for the `test-run-execution pics-export` command."""

import os
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.test_run_execution import test_run_execution
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestPicsExportCommand:
    """Test cases for the `test-run-execution pics-export` command."""

    def test_pics_export_writes_default_filename(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """When no --output-file is given, the file is named after the execution title."""
        api = mock_sync_apis.test_run_executions_api
        api.pics_export_api_v1_test_run_executions__id__pics_export_get.return_value = b"zip-bytes"
        api.read_test_run_execution_api_v1_test_run_executions__id__get.return_value = api_models.TestRunExecution(
            id=1, title="My Execution!", state=api_models.TestStateEnum.passed, project_id=1
        )

        with cli_runner.isolated_filesystem():
            with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(test_run_execution, ["pics-export", "--id", "1"])

            assert result.exit_code == 0
            assert os.path.exists("MyExecution-pics.zip")
            with open("MyExecution-pics.zip", "rb") as f:
                assert f.read() == b"zip-bytes"

        api.pics_export_api_v1_test_run_executions__id__pics_export_get.assert_called_once_with(id=1)

    def test_pics_export_writes_custom_output_file(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """When --output-file is given, the export is written there and read_test_run_execution
        is not called to derive a filename."""
        api = mock_sync_apis.test_run_executions_api
        api.pics_export_api_v1_test_run_executions__id__pics_export_get.return_value = b"zip-bytes"

        with cli_runner.isolated_filesystem():
            with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(test_run_execution, ["pics-export", "--id", "1", "--output-file", "out.zip"])

            assert result.exit_code == 0
            assert os.path.exists("out.zip")

        api.read_test_run_execution_api_v1_test_run_executions__id__get.assert_not_called()

    def test_pics_export_no_content(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """If the API ever returns an empty-but-successful response, a message is
        printed and no file is written (the backend normally 404s instead, see
        test_pics_export_no_pics_used_api_error)."""
        api = mock_sync_apis.test_run_executions_api
        api.pics_export_api_v1_test_run_executions__id__pics_export_get.return_value = None

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["pics-export", "--id", "1"])

        assert result.exit_code == 0
        assert "No PICS content was returned for this test run execution." in result.output

    def test_pics_export_no_pics_used_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """When the execution used no PICS, the backend 404s and the CLI surfaces it."""
        api = mock_sync_apis.test_run_executions_api
        api.pics_export_api_v1_test_run_executions__id__pics_export_get.side_effect = UnexpectedResponse(
            status_code=404,
            content=b"No PICS were used by this test run execution",
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["pics-export", "--id", "1"])

        error_text = (
            "Error: Failed to fetch test run execution PICS export (Status: 404)"
            " - No PICS were used by this test run execution"
        )
        assert result.exit_code == 1
        assert error_text in result.output

    def test_pics_export_configuration_error(self, cli_runner: CliRunner) -> None:
        """A ConfigurationError from get_client is surfaced to the user."""
        with patch(
            "th_cli.commands.test_run_execution.get_client",
            side_effect=ConfigurationError("Could not connect to server"),
        ):
            result = cli_runner.invoke(test_run_execution, ["pics-export", "--id", "1"])

        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_pics_export_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """An UnexpectedResponse from the API is surfaced to the user."""
        api = mock_sync_apis.test_run_executions_api
        api.pics_export_api_v1_test_run_executions__id__pics_export_get.side_effect = UnexpectedResponse(
            status_code=404,
            content=b"Test run execution not found",
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["pics-export", "--id", "999"])

        error_text = (
            "Error: Failed to fetch test run execution PICS export (Status: 404) - Test run execution not found"
        )
        assert result.exit_code == 1
        assert error_text in result.output

    def test_pics_export_requires_id(self, cli_runner: CliRunner) -> None:
        """The --id parameter is required."""
        result = cli_runner.invoke(test_run_execution, ["pics-export"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--id" in result.output
