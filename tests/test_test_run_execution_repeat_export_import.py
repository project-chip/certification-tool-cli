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
"""Tests for the `test-run-execution repeat/export/import` commands."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner
from httpx import ReadTimeout

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import ResponseHandlingException, UnexpectedResponse
from th_cli.commands.test_run_execution import test_run_execution
from th_cli.exceptions import ConfigurationError


def _make_exported_execution(title: str = "My Execution!") -> api_models.ExportedTestRunExecution:
    """Build a minimal ExportedTestRunExecution for export/import round-trip tests."""
    from datetime import datetime, timezone

    return api_models.ExportedTestRunExecution(
        db_revision="abc123",
        test_run_execution=api_models.TestRunExecutionToExport(
            title=title,
            state=api_models.TestStateEnum.passed,
            created_at=datetime.now(timezone.utc),
            log=[],
        ),
    )


@pytest.mark.unit
@pytest.mark.cli
class TestRepeatCommand:
    """Test cases for the `test-run-execution repeat` command."""

    @pytest.fixture(autouse=True)
    def mock_test_logging(self):
        """Patch th_cli.test_run.logging so tests don't start a real LogStreamHandler
        (and its daemon HTTP server) for every invocation."""
        with patch("th_cli.commands.test_run_execution.test_logging") as mock_logging:
            mock_logging.configure_logger_for_run.return_value = "/tmp/test_run.log"
            mock_logging.get_log_stream_url.return_value = None
            yield mock_logging

    def test_repeat_success(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        mock_test_logging: Mock,
    ) -> None:
        """By default, repeat creates the new execution, starts it, and attaches to it the
        same way `run-tests` does (and the frontend's 'Repeat' action does): streaming live
        progress instead of just reporting a static message."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.return_value = (
            sample_test_run_execution
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.return_value = (
            sample_test_run_execution
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.test_run_execution.TestRunSocket") as mock_socket_class,
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 0
        assert f"repeated as new execution {sample_test_run_execution.id}" in result.output
        assert sample_test_run_execution.title in result.output
        assert "Starting Test run" in result.output
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.assert_called_once_with(
            id=1, title=None
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.assert_called_once_with(
            id=sample_test_run_execution.id
        )
        mock_test_logging.configure_logger_for_run.assert_called_once_with(
            title=sample_test_run_execution.title, enable_log_streaming=True
        )
        mock_socket_class.assert_called_once_with(
            sample_test_run_execution, project_config_dict=sample_test_run_execution.execution_config or {}
        )
        mock_socket.connect_websocket.assert_called_once()
        assert mock_socket.run == sample_test_run_execution
        mock_test_logging.stop_log_streaming.assert_called_once()
        mock_api_client.aclose.assert_called_once()

    def test_repeat_with_custom_title(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
    ) -> None:
        """--title is forwarded to the API call."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.return_value = (
            sample_test_run_execution
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.return_value = (
            sample_test_run_execution
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.test_run_execution.TestRunSocket") as mock_socket_class,
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1", "--title", "Custom Title"])

        assert result.exit_code == 0
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.assert_called_once_with(
            id=1, title="Custom Title"
        )

    def test_repeat_start_api_error(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        mock_test_logging: Mock,
    ) -> None:
        """A failure to start the repeated execution is surfaced via the standard error-handling path,
        and the log streaming server started for the run is still stopped."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.return_value = (
            sample_test_run_execution
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.side_effect = UnexpectedResponse(
            status_code=500, content=b"Internal Server Error"
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.test_run_execution.TestRunSocket") as mock_socket_class,
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 1
        assert (
            f"Failed to start repeated test run execution '{sample_test_run_execution.id}' "
            "(Status: 500) - Internal Server Error" in result.output
        )
        mock_test_logging.stop_log_streaming.assert_called_once()

    def test_repeat_start_conflict(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        mock_test_logging: Mock,
    ) -> None:
        """A 409 (e.g. test engine busy) makes clear the execution was still created, and the
        log streaming server started for the run is still stopped."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.return_value = (
            sample_test_run_execution
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.side_effect = UnexpectedResponse(
            status_code=409, content={"detail": "Test Engine is busy."}
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.test_run_execution.TestRunSocket") as mock_socket_class,
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 1
        assert f"Execution {sample_test_run_execution.id} was created but could not be started" in result.output
        assert "Test Engine is busy." in result.output
        mock_test_logging.stop_log_streaming.assert_called_once()

    def test_repeat_start_timeout(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        mock_test_logging: Mock,
    ) -> None:
        """A timeout while starting the repeated execution is surfaced as a clean, readable
        error instead of a raw traceback, and the log streaming server started for the run
        is still stopped."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.return_value = (
            sample_test_run_execution
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.side_effect = (
            ResponseHandlingException(ReadTimeout("timed out"))
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.test_run_execution.TestRunSocket") as mock_socket_class,
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 1
        assert "Timed out waiting for the server" in result.output
        mock_test_logging.stop_log_streaming.assert_called_once()

    def test_repeat_websocket_connect_failure(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        mock_test_logging: Mock,
    ) -> None:
        """An unexpected failure while connecting the websocket (e.g. the backend refuses the
        connection) is surfaced as a clean CLIError instead of a raw Python traceback, and the
        log streaming server started for the run is still stopped."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.return_value = (
            sample_test_run_execution
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.return_value = (
            sample_test_run_execution
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.test_run_execution.TestRunSocket") as mock_socket_class,
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock(side_effect=ConnectionRefusedError("connection refused"))
            mock_socket_class.return_value = mock_socket

            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 1
        assert "Unexpected error during repeated test execution" in result.output
        assert "Traceback" not in result.output
        mock_test_logging.stop_log_streaming.assert_called_once()
        mock_api_client.aclose.assert_called_once()

    def test_repeat_not_found(self, cli_runner: CliRunner, mock_async_apis: Mock, mock_api_client: Mock) -> None:
        """A 404 from the API is surfaced as a clear 'not found' error, and nothing is started."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.side_effect = UnexpectedResponse(
            status_code=404, content={"detail": "TestRunExecution not found"}
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
        ):
            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "999"])

        assert result.exit_code == 1
        assert "Test run execution with ID '999' not found." in result.output
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.assert_not_called()

    def test_repeat_other_api_error(
        self, cli_runner: CliRunner, mock_async_apis: Mock, mock_api_client: Mock
    ) -> None:
        """A non-404 API error is surfaced via the standard error-handling path, and nothing is started."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.side_effect = UnexpectedResponse(
            status_code=500, content=b"Internal Server Error"
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
        ):
            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 1
        assert "Failed to repeat test run execution '1' (Status: 500) - Internal Server Error" in result.output
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.assert_not_called()

    def test_repeat_timeout_error(
        self, cli_runner: CliRunner, mock_async_apis: Mock, mock_api_client: Mock
    ) -> None:
        """A timeout while repeating the execution is surfaced as a clean, readable error
        instead of a raw traceback (the original bug report for this command)."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.side_effect = (
            ResponseHandlingException(ReadTimeout("timed out"))
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
        ):
            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 1
        assert "Timed out waiting for the server" in result.output

    def test_repeat_configuration_error(self, cli_runner: CliRunner) -> None:
        """A ConfigurationError from get_client is surfaced to the user."""
        with patch(
            "th_cli.commands.test_run_execution.get_client",
            side_effect=ConfigurationError("Could not connect to server"),
        ):
            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1"])

        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_repeat_requires_id(self, cli_runner: CliRunner) -> None:
        """The --id parameter is required."""
        result = cli_runner.invoke(test_run_execution, ["repeat"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--id" in result.output

    def test_repeat_no_streaming_disables_log_viewer(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        mock_test_logging: Mock,
    ) -> None:
        """--no-streaming disables the real-time web log viewer for the new execution."""
        api = mock_async_apis.test_run_executions_api
        api.repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post.return_value = (
            sample_test_run_execution
        )
        api.start_test_run_execution_api_v1_test_run_executions__id__start_post.return_value = (
            sample_test_run_execution
        )

        with (
            patch("th_cli.commands.test_run_execution.get_client", return_value=mock_api_client),
            patch("th_cli.commands.test_run_execution.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.test_run_execution.TestRunSocket") as mock_socket_class,
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            result = cli_runner.invoke(test_run_execution, ["repeat", "--id", "1", "--no-streaming"])

        assert result.exit_code == 0
        mock_test_logging.configure_logger_for_run.assert_called_once_with(
            title=sample_test_run_execution.title, enable_log_streaming=False
        )

    def test_repeat_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the repeat command."""
        result = cli_runner.invoke(test_run_execution, ["repeat", "--help"])

        assert result.exit_code == 0
        assert "--id" in result.output
        assert "--title" in result.output
        assert "--no-color" in result.output
        assert "--no-streaming" in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestExportExecutionCommand:
    """Test cases for the `test-run-execution export` command."""

    def test_export_success_default_filename(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """When no --output-file is given, the file is named after the execution title."""
        exported = _make_exported_execution(title="My Execution!")
        api = mock_sync_apis.test_run_executions_api
        api.export_test_run_execution_api_v1_test_run_executions__id__export_get.return_value = exported

        with cli_runner.isolated_filesystem():
            with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(test_run_execution, ["export", "--id", "1"])

            assert result.exit_code == 0
            assert Path("MyExecution-execution.json").exists()
            saved = json.loads(Path("MyExecution-execution.json").read_text())
            assert saved["test_run_execution"]["title"] == "My Execution!"

        api.export_test_run_execution_api_v1_test_run_executions__id__export_get.assert_called_once_with(id=1)

    def test_export_success_custom_filename(self, cli_runner: CliRunner, mock_sync_apis: Mock, temp_dir: Path) -> None:
        """When --output-file is given, the export is written there."""
        exported = _make_exported_execution()
        api = mock_sync_apis.test_run_executions_api
        api.export_test_run_execution_api_v1_test_run_executions__id__export_get.return_value = exported
        output_path = str(temp_dir / "run-42.json")

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["export", "--id", "42", "--output-file", output_path])

        assert result.exit_code == 0
        assert f"exported to '{output_path}'" in result.output
        assert Path(output_path).exists()

    def test_export_not_found(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """A 404 from the API is surfaced as a clear 'not found' error."""
        api = mock_sync_apis.test_run_executions_api
        api.export_test_run_execution_api_v1_test_run_executions__id__export_get.side_effect = UnexpectedResponse(
            status_code=404, content={"detail": "Test Run Execution with id 999 not found"}
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["export", "--id", "999"])

        assert result.exit_code == 1
        assert "Test run execution with ID '999' not found." in result.output

    def test_export_write_failure_raises_cli_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """A file-write failure after a successful export request is surfaced as a clean CLIError."""
        exported = _make_exported_execution()
        api = mock_sync_apis.test_run_executions_api
        api.export_test_run_execution_api_v1_test_run_executions__id__export_get.return_value = exported

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            with patch("pathlib.Path.write_text", side_effect=OSError("Permission denied")):
                result = cli_runner.invoke(
                    test_run_execution, ["export", "--id", "1", "--output-file", "/no/such/dir/out.json"]
                )

        assert result.exit_code == 1
        assert "Failed to write export file '/no/such/dir/out.json'" in result.output
        assert "Permission denied" in result.output

    def test_export_timeout_error(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """A timeout while exporting is surfaced as a clean, readable error instead of a raw
        traceback (the original bug report for this command)."""
        api = mock_sync_apis.test_run_executions_api
        api.export_test_run_execution_api_v1_test_run_executions__id__export_get.side_effect = (
            ResponseHandlingException(ReadTimeout("timed out"))
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["export", "--id", "1"])

        assert result.exit_code == 1
        assert "Timed out waiting for the server" in result.output

    def test_export_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the export command."""
        result = cli_runner.invoke(test_run_execution, ["export", "--help"])

        assert result.exit_code == 0
        assert "--id" in result.output
        assert "--output-file" in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestImportExecutionCommand:
    """Test cases for the `test-run-execution import` command."""

    def test_import_success(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        temp_dir: Path,
    ) -> None:
        """A successful import reports the new execution's ID and title."""
        exported = _make_exported_execution(title="Imported Run")
        import_file = temp_dir / "run.json"
        import_file.write_text(exported.model_dump_json())

        api = mock_sync_apis.test_run_executions_api
        api.import_test_run_execution_api_v1_test_run_executions_import_post.return_value = sample_test_run_execution

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["import", "--file", str(import_file), "--project-id", "7"])

        assert result.exit_code == 0
        assert f"imported as execution {sample_test_run_execution.id}" in result.output
        call_args = api.import_test_run_execution_api_v1_test_run_executions_import_post.call_args
        assert call_args.kwargs["project_id"] == 7
        assert call_args.kwargs["body"].import_file == import_file.read_bytes()

    def test_import_file_not_found(self, cli_runner: CliRunner, mock_sync_apis: Mock) -> None:
        """A non-existent --file is rejected by Click's exists=True validation."""
        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(
                test_run_execution, ["import", "--file", "nonexistent.json", "--project-id", "1"]
            )

        assert result.exit_code == 2
        assert "does not exist" in result.output

    def test_import_db_revision_mismatch(self, cli_runner: CliRunner, mock_sync_apis: Mock, temp_dir: Path) -> None:
        """A db_revision mismatch (422) is surfaced with the backend's plain-text detail."""
        exported = _make_exported_execution()
        import_file = temp_dir / "run.json"
        import_file.write_text(exported.model_dump_json())

        api = mock_sync_apis.test_run_executions_api
        api.import_test_run_execution_api_v1_test_run_executions_import_post.side_effect = UnexpectedResponse(
            status_code=422,
            content={"detail": "Mismatching 'db_revision'. Trying to import from abc123 to def456"},
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["import", "--file", str(import_file), "--project-id", "1"])

        assert result.exit_code == 1
        assert "Mismatching 'db_revision'" in result.output
        assert "{" not in result.output

    def test_import_requires_project_id(self, cli_runner: CliRunner, temp_dir: Path) -> None:
        """The --project-id parameter is required."""
        import_file = temp_dir / "run.json"
        import_file.write_text(_make_exported_execution().model_dump_json())

        result = cli_runner.invoke(test_run_execution, ["import", "--file", str(import_file)])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--project-id" in result.output

    def test_import_timeout_error(self, cli_runner: CliRunner, mock_sync_apis: Mock, temp_dir: Path) -> None:
        """A timeout while importing is surfaced as a clean, readable error instead of a raw
        traceback (the original bug report for this command)."""
        import_file = temp_dir / "run.json"
        import_file.write_text(_make_exported_execution().model_dump_json())

        api = mock_sync_apis.test_run_executions_api
        api.import_test_run_execution_api_v1_test_run_executions_import_post.side_effect = (
            ResponseHandlingException(ReadTimeout("timed out"))
        )

        with patch("th_cli.commands.test_run_execution.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(test_run_execution, ["import", "--file", str(import_file), "--project-id", "1"])

        assert result.exit_code == 1
        assert "Timed out waiting for the server" in result.output

    def test_import_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the import command."""
        result = cli_runner.invoke(test_run_execution, ["import", "--help"])

        assert result.exit_code == 0
        assert "--file" in result.output
        assert "--project-id" in result.output
