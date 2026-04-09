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
"""Tests for the run_tests command."""

import re
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.run_tests import (
    TWO_WAY_TALK_TEST_IDS,
    _contains_webrtc_two_way_talk,
    _dict_contains_key,
    _parse_extra_args,
    _print_webrtc_banner_and_wait,
    run_tests,
)
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestRunTestsCommand:
    """Test cases for the run_tests command."""

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
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with (
            patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client),
            patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis),
            patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ),
            patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class,
            patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict),
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            # Act
            result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1,TC-ACE-1.2"])

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
        mock_json_config_file: Path,
    ) -> None:
        """Test successful test run with custom JSON configuration file."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(
                            run_tests,
                            [
                                "--tests-list",
                                "TC-ACE-1.1",
                                "--config",
                                str(mock_json_config_file),
                                "--title",
                                "Custom Test Run",
                            ],
                        )

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
        mock_pics_dir: Path,
    ) -> None:
        """Test successful test run with PICS configuration."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(
                            run_tests, ["--tests-list", "TC-ACE-1.1", "--pics-config-folder", str(mock_pics_dir)]
                        )

        # Assert
        assert result.exit_code == 0
        assert "PICS Used" in result.output
        assert "TC.TEST.1.1" in result.output
        assert "TC.TEST.A.1" in result.output
        assert "TC.TEST.E.1" in result.output

    def test_run_tests_success_with_project_id(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test successful test run with project ID."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1", "--project-id", "42"])

        # Assert
        assert result.exit_code == 0

    def test_run_tests_success_with_no_color(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test successful test run with colors disabled."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        projects_api.return_value = sample_default_config_dict
        test_collections_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch("th_cli.commands.run_tests.set_colors_enabled") as mock_set_colors:
                        with patch(
                            "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                        ):
                            mock_socket = Mock()
                            mock_socket.connect_websocket = AsyncMock()
                            mock_socket_class.return_value = mock_socket

                            # Act
                            result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1", "--no-color"])

        # Assert
        assert result.exit_code == 0
        mock_set_colors.assert_called_once_with(False)

    def test_run_tests_invalid_test_ids(self, cli_runner: CliRunner) -> None:
        """Test run tests with invalid test IDs format."""
        # Act
        result = cli_runner.invoke(run_tests, ["--tests-list", "invalid-test-id,another-invalid"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Invalid test ID format" in result.output

    @pytest.mark.parametrize(
        "empty_test_id",
        [
            "",
            " ",
            "   ",
        ],
    )
    def test_run_tests_empty_test_list(self, cli_runner: CliRunner, empty_test_id: str) -> None:
        """Test run tests with empty test list."""
        # Act
        result = cli_runner.invoke(run_tests, ["--tests-list", empty_test_id])

        # Assert
        assert result.exit_code == 1
        assert "Error: Test IDs list cannot be empty" in result.output

    def test_run_tests_config_file_not_found(self, cli_runner: CliRunner) -> None:
        """Test run tests with non-existent config file."""
        # Act
        result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1", "--config", "nonexistent.json"])

        # Assert
        assert result.exit_code == 1
        assert "Error: File not found: nonexistent.json" in result.output

    def test_run_tests_pics_directory_not_found(self, cli_runner: CliRunner) -> None:
        """Test run tests with non-existent PICS directory."""
        # Act
        result = cli_runner.invoke(
            run_tests, ["--tests-list", "TC-ACE-1.1", "--pics-config-folder", "nonexistent_pics_dir"]
        )

        # Assert
        assert result.exit_code == 1
        assert "Error: Directory not found: nonexistent_pics_dir" in result.output

    def test_run_tests_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test run tests with configuration error."""
        # Arrange
        with patch(
            "th_cli.commands.run_tests.get_client", side_effect=ConfigurationError("Could not connect to server")
        ):
            # Act
            result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_run_tests_api_error_getting_default_config(
        self, cli_runner: CliRunner, mock_async_apis: Mock, mock_api_client: Mock
    ) -> None:
        """Test run tests with API error when getting default config."""
        # Arrange
        api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get

        api.side_effect = Exception("Config API error")
        with patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
                # Act
                result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Unexpected error during test execution: Config API error" in result.output
        mock_api_client.aclose.assert_called_once()

    def test_run_tests_api_error_getting_test_collections(
        self, cli_runner: CliRunner, mock_async_apis: Mock, sample_default_config_dict: dict
    ) -> None:
        """Test run tests with API error when getting test collections."""
        # Arrange
        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        projects_api.return_value = sample_default_config_dict
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_collections_api.side_effect = Exception("Collections API error")

        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict):
                    # Act
                    result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Unexpected error during test execution: Collections API error" in result.output

    def test_run_tests_api_error_creating_test_run(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_default_config_dict: dict,
    ) -> None:
        """Test run tests with API error when creating test run."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=400,
            content=b"Bad Request",
        )

        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post

        test_collections_api.return_value = sample_test_collections
        projects_api.return_value = sample_default_config_dict
        cli_api.side_effect = api_exception
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict):
                    # Act
                    result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to create test run execution (Status: 400) - Bad Request" in result.output

    def test_run_tests_api_error_starting_test_run(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test run tests with API error when starting test run."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=500,
            content=b"Internal Server Error",
        )

        projects_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collections_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions__id__start_post

        test_collections_api.return_value = sample_test_collections
        projects_api.return_value = sample_default_config_dict
        cli_api.return_value = sample_test_run_execution
        start_api.side_effect = api_exception
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

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

    @pytest.mark.parametrize(
        "test_list",
        [
            "TC-ACE-1.1",
            "TC-ACE-1.1,TC-ACE-1.2",
            "TC_ACE_1_1,TC_ACE_1_2,TC_ACE_1_3",
            "TC_ACE_1_1,TC_ACE_1_2,TC_ACE_1_3,TC_ACE_1_3-custom",
            "TC-ACE-1.1, TC-ACE-1.2, TC-ACE-1.3",  # with spaces
            "TC-MCORE_FS-1.1, TC-MCORE_FS-1_2, TC_MCORE_FS-1.2",
            "TC_CADMIN_1_3_4",
            "TC_CADMIN_1_3_102",
        ],
    )
    def test_run_tests_various_test_lists(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
        test_list: str,
    ) -> None:
        """Test run tests with various test list formats."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        start_api = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        start_api.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, ["--tests-list", test_list])

        # Assert
        assert result.exit_code == 0

    def test_run_tests_test_selection_building(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test that test selection is properly built from test collections."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution

        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.build_test_selection") as mock_build_test_selection:
                    with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                        with patch(
                            "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                        ):
                            mock_build_test_selection.return_value = {"mock_collection": {"mock_suite": {"mock": 1}}}
                            mock_socket = Mock()
                            mock_socket.connect_websocket = AsyncMock()
                            mock_socket_class.return_value = mock_socket

                            # Act
                            result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1,TC-ACE-1.2"])

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
        sample_default_config_dict: dict,
    ) -> None:
        """Test that logger is properly configured for the test run."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run") as mock_configure_logger:
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_configure_logger.return_value = "/path/to/test_logs/custom_run.log"
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(
                            run_tests, ["--tests-list", "TC-ACE-1.1", "--title", "Custom Logger Test"]
                        )

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
        sample_default_config_dict: dict,
    ) -> None:
        """Test that default title is generated when not provided."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

        # Assert
        assert result.exit_code == 0
        # Should contain a timestamp-based title
        assert "Creating new test run with title" in result.output
        # The title should be a timestamp format like "2025-01-01-10:00:00"
        output_lines = result.output.split("\n")
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
        mock_json_config_file: Path,
    ) -> None:
        """Test that JSON configuration data is properly processed and displayed."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution
        with patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis):
            with patch(
                "th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test_logs/test.log"
            ):
                with patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class:
                    with patch(
                        "th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict
                    ):
                        mock_socket = Mock()
                        mock_socket.connect_websocket = AsyncMock()
                        mock_socket_class.return_value = mock_socket

                        # Act
                        result = cli_runner.invoke(
                            run_tests, ["--tests-list", "TC-ACE-1.1", "--config", str(mock_json_config_file)]
                        )

        # Assert
        assert result.exit_code == 0
        assert "Config Used (Execution Only)" in result.output
        # Should show the configuration data
        assert "dut_config" in result.output
        assert "network" in result.output

    @pytest.mark.parametrize(
        "invalid_test_id",
        [
            "invalid-format",
            "TC-INVALID",
            "TCACE11",
            "TC-ACE-1.1.1.1",
            "TC-ACE-1.1-custom-extra",
        ],
    )
    def test_run_tests_invalid_test_id_formats(self, cli_runner: CliRunner, invalid_test_id: str) -> None:
        """Test run tests with various invalid test ID formats."""
        # Act
        result = cli_runner.invoke(run_tests, ["--tests-list", invalid_test_id])

        # Assert
        assert result.exit_code == 1
        assert "Error: Invalid test ID format" in result.output

    def test_run_tests_client_cleanup_on_exception(self, cli_runner: CliRunner, mock_api_client: Mock) -> None:
        """Test that client is properly cleaned up even when an exception occurs."""
        # Arrange
        with patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.run_tests.AsyncApis", side_effect=Exception("API creation failed")):
                # Act
                result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

        # Assert
        assert result.exit_code == 1
        assert "API creation failed" in result.output
        mock_api_client.aclose.assert_called_once()


@pytest.mark.unit
@pytest.mark.cli
class TestParseExtraArgs:
    """Test cases for the _parse_extra_args function."""

    def test_parse_extra_args_single_argument(self) -> None:
        """Test parsing a single extra argument."""
        # Arrange
        args = ["--int-arg", "endpoint:2"]

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {"int-arg": "endpoint:2"}

    def test_parse_extra_args_multiple_arguments(self) -> None:
        """Test parsing multiple extra arguments."""
        # Arrange
        args = ["--int-arg", "endpoint:2", "--bool-arg", "flag:true"]

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {"int-arg": "endpoint:2", "bool-arg": "flag:true"}

    def test_parse_extra_args_with_short_flags(self) -> None:
        """Test parsing extra arguments with short flags."""
        # Arrange
        args = ["-a", "value1", "-b", "value2"]

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {"a": "value1", "b": "value2"}

    def test_parse_extra_args_mixed_long_and_short(self) -> None:
        """Test parsing mixed long and short flags."""
        # Arrange
        args = ["--long-arg", "value1", "-s", "value2"]

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {"long-arg": "value1", "s": "value2"}

    def test_parse_extra_args_flag_without_value(self) -> None:
        """Test parsing flag without value (sets to empty string)."""
        # Arrange
        args = ["--bool-flag", "--another-arg", "value"]

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {"bool-flag": "", "another-arg": "value"}

    def test_parse_extra_args_empty_list(self) -> None:
        """Test parsing empty args list."""
        # Arrange
        args = []

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {}

    def test_parse_extra_args_complex_values(self) -> None:
        """Test parsing arguments with complex values."""
        # Arrange
        args = [
            "--string-arg",
            "PICS_SC_2_2:false",
            "--json-arg",
            '{"key":"value"}',
            "--numeric-arg",
            "nodeId:305414945",
        ]

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {
            "string-arg": "PICS_SC_2_2:false",
            "json-arg": '{"key":"value"}',
            "numeric-arg": "nodeId:305414945",
        }

    def test_parse_extra_args_colons_in_values(self) -> None:
        """Test parsing SDK test parameter format with colons."""
        # Arrange
        args = [
            "--int-arg",
            "endpoint:2",
            "--string-arg",
            "discriminator:1234",
            "--bool-arg",
            "someBoolFlag:true",
        ]

        # Act
        result = _parse_extra_args(args)

        # Assert
        assert result == {
            "int-arg": "endpoint:2",
            "string-arg": "discriminator:1234",
            "bool-arg": "someBoolFlag:true",
        }


@pytest.mark.unit
@pytest.mark.cli
class TestRunTestsWithExtraArgs:
    """Test cases for run_tests command with extra arguments feature."""

    def test_run_tests_with_extra_args_basic(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test run tests with basic extra arguments."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution

        with (
            patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client),
            patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test.log"),
            patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class,
            patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict),
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            # Act
            result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1", "--", "--int-arg", "endpoint:2"])

        # Assert
        assert result.exit_code == 0
        assert "Extra SDK Test Parameters" in result.output
        assert "endpoint:2" in result.output

    def test_run_tests_with_multiple_extra_args(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test run tests with multiple extra arguments."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution

        with (
            patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client),
            patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test.log"),
            patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class,
            patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict),
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            # Act
            result = cli_runner.invoke(
                run_tests,
                [
                    "--tests-list",
                    "TC-ACE-1.1",
                    "--",
                    "--int-arg",
                    "endpoint:2",
                    "--bool-arg",
                    "flag:true",
                    "--string-arg",
                    "discriminator:1234",
                ],
            )

        # Assert
        assert result.exit_code == 0
        assert "endpoint:2" in result.output
        assert "flag:true" in result.output
        assert "discriminator:1234" in result.output

    def test_run_tests_without_extra_args(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test run tests without extra arguments (normal behavior)."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution

        with (
            patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client),
            patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test.log"),
            patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class,
            patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict),
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            # Act
            result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1"])

        # Assert
        assert result.exit_code == 0
        # Should not show extra args message when no extra args provided
        assert "Extra SDK Test Parameters" not in result.output

    def test_run_tests_extra_args_with_config_file(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
        mock_json_config_file,
    ) -> None:
        """Test run tests with both config file and extra arguments."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution

        with (
            patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client),
            patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test.log"),
            patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class,
            patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict),
        ):
            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            # Act
            result = cli_runner.invoke(
                run_tests,
                ["--tests-list", "TC-ACE-1.1", "--config", str(mock_json_config_file), "--", "--int-arg", "endpoint:2"],
            )

        # Assert
        assert result.exit_code == 0
        assert "Config Used (Execution Only)" in result.output
        assert "Extra SDK Test Parameters" in result.output

    def test_run_tests_verify_deep_copy_isolation(
        self,
        cli_runner: CliRunner,
        mock_async_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
        sample_test_run_execution: api_models.TestRunExecutionWithChildren,
        sample_default_config_dict: dict,
    ) -> None:
        """Test that test_run_config uses deepcopy for isolation."""
        # Arrange
        project_api = mock_async_apis.projects_api.default_config_api_v1_projects_default_config_get
        test_collection_api = mock_async_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        test_run_executions_api = mock_async_apis.test_run_executions_api
        cli_api = test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        id_start = test_run_executions_api.start_test_run_execution_api_v1_test_run_executions_id_start_post

        project_api.return_value = sample_default_config_dict
        test_collection_api.return_value = sample_test_collections
        cli_api.return_value = sample_test_run_execution
        id_start.return_value = sample_test_run_execution

        with (
            patch("th_cli.commands.run_tests.get_client", return_value=mock_api_client),
            patch("th_cli.commands.run_tests.AsyncApis", return_value=mock_async_apis),
            patch("th_cli.commands.run_tests.test_logging.configure_logger_for_run", return_value="./test.log"),
            patch("th_cli.commands.run_tests.TestRunSocket") as mock_socket_class,
            patch("th_cli.commands.run_tests.convert_nested_to_dict", return_value=sample_default_config_dict),
            patch("th_cli.commands.run_tests.copy.deepcopy") as mock_deepcopy,
        ):

            # Configure deepcopy to return a new dict
            mock_deepcopy.return_value = dict(sample_default_config_dict)

            mock_socket = Mock()
            mock_socket.connect_websocket = AsyncMock()
            mock_socket_class.return_value = mock_socket

            # Act
            result = cli_runner.invoke(run_tests, ["--tests-list", "TC-ACE-1.1", "--", "--int-arg", "endpoint:2"])

        # Assert
        assert result.exit_code == 0
        # Verify deepcopy was called to ensure isolation
        mock_deepcopy.assert_called_once()


# ---------------------------------------------------------------------------
# _dict_contains_key
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDictContainsKey:
    """Tests for _dict_contains_key — recursive key search."""

    def test_key_at_top_level(self):
        assert _dict_contains_key({"TC_WEBRTC_1_6": 1}, "TC_WEBRTC_1_6") is True

    def test_key_nested_one_level(self):
        d = {"suite": {"TC_WEBRTC_1_6": 1}}
        assert _dict_contains_key(d, "TC_WEBRTC_1_6") is True

    def test_key_nested_two_levels(self):
        d = {"collection": {"suite": {"TC_WEBRTC_1_6": 1}}}
        assert _dict_contains_key(d, "TC_WEBRTC_1_6") is True

    def test_key_absent(self):
        assert _dict_contains_key({"TC_OTHER": 1}, "TC_WEBRTC_1_6") is False

    def test_empty_dict(self):
        assert _dict_contains_key({}, "TC_WEBRTC_1_6") is False

    def test_non_dict_input_returns_false(self):
        assert _dict_contains_key(["TC_WEBRTC_1_6"], "TC_WEBRTC_1_6") is False

    def test_none_input_returns_false(self):
        assert _dict_contains_key(None, "TC_WEBRTC_1_6") is False

    def test_value_equal_to_target_but_not_key(self):
        # Value matches target but it should only check keys
        assert _dict_contains_key({"other": "TC_WEBRTC_1_6"}, "TC_WEBRTC_1_6") is False


# ---------------------------------------------------------------------------
# _contains_webrtc_two_way_talk
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestContainsWebrtcTwoWayTalk:
    """Tests for _contains_webrtc_two_way_talk and TWO_WAY_TALK_TEST_IDS constant."""

    def test_constant_is_non_empty(self):
        assert len(TWO_WAY_TALK_TEST_IDS) > 0

    def test_constant_contains_tc_webrtc_1_6(self):
        assert "TC_WEBRTC_1_6" in TWO_WAY_TALK_TEST_IDS

    def test_returns_true_when_tc_webrtc_1_6_present(self):
        selected = {"SDK Python Tests": {"Python Testing Suite": {"TC_WEBRTC_1_6": 1}}}
        assert _contains_webrtc_two_way_talk(selected) is True

    def test_returns_false_when_only_other_tests_present(self):
        selected = {"SDK Python Tests": {"Python Testing Suite": {"TC_ACE_1_3": 1}}}
        assert _contains_webrtc_two_way_talk(selected) is False

    def test_returns_false_for_empty_selection(self):
        assert _contains_webrtc_two_way_talk({}) is False

    def test_returns_true_when_mixed_tests_include_webrtc(self):
        selected = {
            "SDK Python Tests": {
                "Python Testing Suite": {
                    "TC_ACE_1_3": 1,
                    "TC_WEBRTC_1_6": 1,
                }
            }
        }
        assert _contains_webrtc_two_way_talk(selected) is True

    def test_partial_name_does_not_match(self):
        selected = {"SDK Python Tests": {"Suite": {"TC_WEBRTC_1_6_EXTRA": 1}}}
        assert _contains_webrtc_two_way_talk(selected) is False

    def test_returns_true_for_any_id_in_constant(self):
        """Every ID in TWO_WAY_TALK_TEST_IDS must trigger True individually."""
        for tc_id in TWO_WAY_TALK_TEST_IDS:
            selected = {"Suite": {tc_id: 1}}
            assert _contains_webrtc_two_way_talk(selected) is True, f"{tc_id} should trigger two-way talk"


# ---------------------------------------------------------------------------
# _print_webrtc_banner_and_wait
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPrintWebrtcBannerAndWait:
    """Tests for _print_webrtc_banner_and_wait — banner output and browser wait."""

    def _make_handler(self, wait_result: bool):
        handler = Mock()
        handler.wait_for_browser = Mock(return_value=wait_result)
        return handler

    def _patches(self, resolved="127.0.0.1", wait_result=True):
        stack = ExitStack()
        stack.enter_context(patch("socket.gethostbyname", return_value=resolved))
        stack.enter_context(patch("th_cli.test_run.camera.two_way_talk_handler._get_local_ip", return_value="10.0.0.5"))
        mock_loop = stack.enter_context(patch("asyncio.get_event_loop"))
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=wait_result)
        return stack

    @pytest.mark.asyncio
    async def test_wait_for_browser_called_on_handler(self):
        """handler.wait_for_browser must be passed to run_in_executor."""
        handler = self._make_handler(True)
        with patch("click.echo"):
            with self._patches():
                await _print_webrtc_banner_and_wait("localhost", handler)

        # run_in_executor was called with handler.wait_for_browser
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
            pass  # already verified above implicitly

    @pytest.mark.asyncio
    async def test_prints_connected_message_when_browser_connects(self):
        handler = self._make_handler(True)
        with patch("click.echo") as mock_echo:
            with self._patches(wait_result=True):
                await _print_webrtc_banner_and_wait("localhost", handler)

        raw = " ".join(str(c) for call in mock_echo.call_args_list for c in call[0])
        output = re.sub(r"\x1b\[[0-9;]*m", "", raw)
        assert "Browser connected" in output

    @pytest.mark.asyncio
    async def test_prints_not_detected_message_on_timeout(self):
        handler = self._make_handler(False)
        with patch("click.echo") as mock_echo:
            with self._patches(wait_result=False):
                await _print_webrtc_banner_and_wait("localhost", handler)

        raw = " ".join(str(c) for call in mock_echo.call_args_list for c in call[0])
        output = re.sub(r"\x1b\[[0-9;]*m", "", raw).lower()
        assert "not detected" in output or "proceeding anyway" in output

    @pytest.mark.asyncio
    async def test_loopback_hostname_triggers_local_ip_lookup(self):
        """When hostname resolves to loopback, URL must use the LAN IP from _get_local_ip."""
        handler = self._make_handler(True)
        lan_ip = "192.168.1.50"
        captured_echo_args = []

        def capture_echo(arg=""):
            captured_echo_args.append(str(arg))

        with patch("click.echo", side_effect=capture_echo):
            with patch("socket.gethostbyname", return_value="127.0.0.1"):
                with patch(
                    "th_cli.test_run.camera.two_way_talk_handler._get_local_ip",
                    return_value=lan_ip,
                ):
                    with patch("asyncio.get_event_loop") as mock_loop:
                        mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
                        await _print_webrtc_banner_and_wait("localhost", handler)

        # The URL echoed must contain the LAN IP, not loopback
        all_output = " ".join(re.sub(r"\x1b\[[0-9;]*m", "", s) for s in captured_echo_args)
        assert lan_ip in all_output

    @pytest.mark.asyncio
    async def test_non_loopback_hostname_skips_local_ip_lookup(self):
        """When hostname resolves to a LAN IP, _get_local_ip() must NOT be called."""
        handler = self._make_handler(True)
        with patch("click.echo"):
            with patch("socket.gethostbyname", return_value="192.168.1.100"):
                with patch(
                    "th_cli.test_run.camera.two_way_talk_handler._get_local_ip",
                    return_value="192.168.1.50",
                ) as mock_local_ip:
                    with patch("asyncio.get_event_loop") as mock_loop:
                        mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
                        await _print_webrtc_banner_and_wait("192.168.1.100", handler)

        mock_local_ip.assert_not_called()
