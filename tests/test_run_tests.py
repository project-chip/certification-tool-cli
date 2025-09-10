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
"""Tests for the run_tests command."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner
from httpx import Headers

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.run_tests import run_tests
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestRunTestsCommand:
    """Test cases for the run_tests command."""

    @pytest.fixture
    def sample_default_config_dict(self) -> dict:
        """Create a sample default configuration dictionary."""
        return {
            "network": {
                "wifi": {
                    "ssid": "default_wifi",
                    "password": "default_password"
                },
                "thread": {
                    "operational_dataset_hex": "default_hex"
                }
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": "3840",
                "trace_log": False
            }
        }

    def test_run_tests_success_minimal_args(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test successful test run with minimal arguments."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client), \
            patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis), \
            patch(
            "th_cli.commands.run_tests.test_logging.configure_logger_for_run",
            return_value="./test_logs/test.log"), \
            patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class, \
            patch(
                "th_cli.commands.run_tests.convert_nested_to_dict",
                return_value=sample_default_config_dict
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            # Act
            result = cli_runner.invoke(run_tests, [
                "--tests-list", "TC-ACE-1.1,TC-ACE-1.2"
            ])

        # Assert
        assert result.exit_code == 0
        assert "Creating new test run with title" in result.output
        assert "Starting Test run" in result.output
        assert "Log output in" in result.output
        mock_api_client.aclose.assert_called_once()

    def test_run_tests_success_with_custom_config(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
        mock_properties_file: Path
    ) -> None:
        """Test successful test run with custom configuration file."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        id_start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict",
                        return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        # pytest.set_trace()
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", "TC-ACE-1.1",
                            "--config", str(mock_properties_file),
                            "--title", "Custom Test Run"
                        ])

        # Assert
        assert result.exit_code == 0
        assert "Creating new test run with title: Custom Test Run" in result.output

    def test_run_tests_success_with_pics_config(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
        mock_pics_dir: Path
    ) -> None:
        """Test successful test run with PICS configuration."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict",
                        return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", "TC-ACE-1.1",
                            "--pics-config-folder", str(mock_pics_dir)
                        ])

        # Assert
        assert result.exit_code == 0
        assert "PICS Used" in result.output

    def test_run_tests_success_with_project_id(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict
    ) -> None:
        """Test successful test run with project ID."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                               return_value=sample_default_config_dict):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", "TC-ACE-1.1",
                            "--project-id", "42"
                        ])

        # Assert
        assert result.exit_code == 0

    def test_run_tests_success_with_no_color(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict
    ) -> None:
        """Test successful test run with colors disabled."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.set_colors_enabled") as mock_set_colors:
                        with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                                   return_value=sample_default_config_dict):
                            mock_socket = Mock()
                            mock_socket.connect_websocket = AsyncMock()
                            mock_socket_class.return_value = mock_socket

                            # Act
                            result = cli_runner.invoke(run_tests, [
                                "--tests-list", "TC-ACE-1.1",
                                "--no-color"
                            ])

        # Assert
        assert result.exit_code == 0
        mock_set_colors.assert_called_once_with(False)

    def test_run_tests_invalid_test_ids(self, cli_runner: CliRunner) -> None:
        """Test run tests with invalid test IDs format."""
        # Act
        result = cli_runner.invoke(run_tests, [
            "--tests-list", "invalid-test-id,another-invalid"
        ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Invalid test ID format" in result.output

    def test_run_tests_empty_test_list(self, cli_runner: CliRunner) -> None:
        """Test run tests with empty test list."""
        # Act
        result = cli_runner.invoke(run_tests, [
            "--tests-list", ""
        ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Test IDs list cannot be empty" in result.output

    def test_run_tests_config_file_not_found(self, cli_runner: CliRunner) -> None:
        """Test run tests with non-existent config file."""
        # Act
        result = cli_runner.invoke(run_tests, [
            "--tests-list", "TC-ACE-1.1",
            "--config", "nonexistent.properties"
        ])

        # Assert
        assert result.exit_code == 1
        assert "Error: File not found: nonexistent.properties" in result.output

    def test_run_tests_pics_directory_not_found(self, cli_runner: CliRunner) -> None:
        """Test run tests with non-existent PICS directory."""
        # Act
        result = cli_runner.invoke(run_tests, [
            "--tests-list", "TC-ACE-1.1",
            "--pics-config-folder", "nonexistent_pics_dir"
        ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Directory not found: nonexistent_pics_dir" in result.output

    def test_run_tests_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test run tests with configuration error."""
        # Arrange
        with patch(
            "th_cli.commands.run_tests.get_client",
            side_effect=ConfigurationError("Could not connect to server")
        ):
            # Act
            result = cli_runner.invoke(run_tests, [
                "--tests-list", "TC-ACE-1.1"
            ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_run_tests_api_error_getting_default_config(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock
    ) -> None:
        """Test run tests with API error when getting default config."""
        # Arrange
        api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get

        api.side_effect = Exception("Config API error")
        with patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
                # Act
                result = cli_runner.invoke(run_tests, [
                    "--tests-list", "TC-ACE-1.1"
                ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Unexpected error during test execution: Config API error" in result.output
        mock_api_client.aclose.assert_called_once()

    def test_run_tests_api_error_getting_test_collections(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_default_config_dict: dict
    ) -> None:
        """Test run tests with API error when getting test collections."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        projects_api.return_value = sample_default_config_dict
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_collections_api.side_effect = Exception("Collections API error")

        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                           return_value=sample_default_config_dict):
                    # Act
                    result = cli_runner.invoke(run_tests, [
                        "--tests-list", "TC-ACE-1.1"
                    ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Unexpected error during test execution: Collections API error" in result.output

    def test_run_tests_api_error_creating_test_run(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_default_config_dict: dict
    ) -> None:
        """Test run tests with API error when creating test run."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=400,
            reason_phrase="Bad Request",
            content=b"Bad Request",
            headers=Headers(),
        )

        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post

        test_collections_api.return_value = sample_test_collections
        projects_api.return_value = sample_default_config_dict
        cli_api.side_effect = api_exception
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                           return_value=sample_default_config_dict):
                    # Act
                    result = cli_runner.invoke(run_tests, [
                        "--tests-list", "TC-ACE-1.1"
                    ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to create test run execution (Status: 400) - Bad Request" in result.output

    def test_run_tests_api_error_starting_test_run(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict
    ) -> None:
        """Test run tests with API error when starting test run."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=500,
            reason_phrase="Internal Server Error",
            content=b"Internal Server Error",
            headers=Headers(),
        )

        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        test_collections_api.return_value = sample_test_collections
        projects_api.return_value = sample_default_config_dict
        cli_api.return_value = sample_test_run_execution
        start_api.side_effect = api_exception
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                               return_value=sample_default_config_dict):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", "TC-ACE-1.1"
                        ])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to start test run (Status: 500) - Internal Server Error" in result.output

    def test_run_tests_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for run_tests command."""
        # Act
        result = cli_runner.invoke(run_tests, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "CLI execution of a test run from selected" in result.output
        assert "--tests-list" in result.output
        assert "--title" in result.output
        assert "--config" in result.output
        assert "--pics-config-folder" in result.output
        assert "--project-id" in result.output
        assert "--no-color" in result.output

    def test_run_tests_required_tests_list_parameter(self, cli_runner: CliRunner) -> None:
        """Test that the --tests-list parameter is required."""
        # Act
        result = cli_runner.invoke(run_tests)

        # Assert
        assert result.exit_code != 0
        assert "required" in result.output

    @pytest.mark.parametrize("test_list", [
        "TC-ACE-1.1",
        "TC-ACE-1.1,TC-ACE-1.2",
        "TC_ACE_1_1,TC_ACE_1_2,TC_ACE_1_3",
        "TC-ACE-1.1, TC-ACE-1.2, TC-ACE-1.3",  # with spaces
    ])
    def test_run_tests_various_test_lists(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
        test_list: str
    ) -> None:
        """Test run tests with various test list formats."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                               return_value=sample_default_config_dict):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", test_list
                        ])

        # Assert
        assert result.exit_code == 0

    def test_run_tests_test_selection_building(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict
    ) -> None:
        """Test that test selection is properly built from test collections."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution

        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.build_test_selection") as mock_build_test_selection:
                    with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                        with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                                   return_value=sample_default_config_dict):
                            mock_build_test_selection.return_value = {"mock_collection": {"mock_suite": {"mock": 1}}}
                            mock_socket = Mock()
                            mock_socket.connect_websocket = AsyncMock()
                            mock_socket_class.return_value = mock_socket

                            # Act
                            result = cli_runner.invoke(run_tests, [
                                "--tests-list", "TC-ACE-1.1,TC-ACE-1.2"
                            ])

        # Assert
        assert result.exit_code == 0
        mock_build_test_selection.assert_called_once()
        # Verify the test selection is displayed
        assert "Selected tests" in result.output

    def test_run_tests_logger_configuration(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict
    ) -> None:
        """Test that logger is properly configured for the test run."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run") as mock_configure_logger:
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                               return_value=sample_default_config_dict):
                        mock_configure_logger.return_value = "/path/to/test_logs/custom_run.log"
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", "TC-ACE-1.1",
                            "--title", "Custom Logger Test"
                        ])

        # Assert
        assert result.exit_code == 0
        mock_configure_logger.assert_called_once_with(title="Custom Logger Test")
        assert "Log output in: /path/to/test_logs/custom_run.log" in result.output

    def test_run_tests_default_title_generation(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict
    ) -> None:
        """Test that default title is generated when not provided."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                               return_value=sample_default_config_dict):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", "TC-ACE-1.1"
                        ])

        # Assert
        assert result.exit_code == 0
        # Should contain a timestamp-based title
        assert "Creating new test run with title" in result.output
        # The title should be a timestamp format like "2025-01-01-10:00:00"
        output_lines = result.output.split('\n')
        title_line = next((line for line in output_lines if "Creating new test run with title" in line), None)
        assert title_line is not None
        # Extract the title part and verify it looks like a timestamp
        title = title_line.split("Creating new test run with title: ")[1]
        # Should contain date and time separators
        assert "-" in title and ":" in title

    def test_run_tests_config_data_processing(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
        mock_properties_file: Path
    ) -> None:
        """Test that configuration data is properly processed and displayed."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections_get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_test_run_execution_cli_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run",
                       return_value="./test_logs/test.log"):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.convert_nested_to_dict",
                               return_value=sample_default_config_dict):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, [
                            "--tests-list", "TC-ACE-1.1",
                            "--config", str(mock_properties_file)
                        ])

        # Assert
        assert result.exit_code == 0
        assert "Read config from file" in result.output
        assert "CLI Config for test run execution" in result.output
        # Should show the configuration data
        assert "dut_config" in result.output
        assert "network" in result.output

    @pytest.mark.parametrize("invalid_test_id", [
        "invalid-format",
        "TC-INVALID",
        "TCACE11",
        "TC-ACE-1.1.1.1",
        "",
        "   ",
    ])
    def test_run_tests_invalid_test_id_formats(
        self,
        cli_runner: CliRunner,
        invalid_test_id: str
    ) -> None:
        """Test run tests with various invalid test ID formats."""
        # Act
        result = cli_runner.invoke(run_tests, [
            "--tests-list", invalid_test_id
        ])

        # Assert
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_run_tests_client_cleanup_on_exception(self, cli_runner: CliRunner, mock_api_client: Mock) -> None:
        """Test that client is properly cleaned up even when an exception occurs."""
        # Arrange
        with patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.run_tests.AsyncApis", side_effect=Exception("API creation failed")):
                # Act
                result = cli_runner.invoke(run_tests, [
                    "--tests-list", "TC-ACE-1.1"
                ])

        # Assert
        assert result.exit_code == 1
        mock_api_client.aclose.assert_called_once()
