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
"""Tests for the project commands (create, delete, list, update)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from httpx import Headers

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.project import project


@pytest.mark.unit
@pytest.mark.cli
class TestCreateProjectCommand:
    """Test cases for the create_project command."""

    def test_create_project_success_with_default_config(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_project: api_models.Project
    ) -> None:
        """Test successful project creation with default configuration."""
        # Arrange
        default_config = api_models.TestEnvironmentConfig(
            network=api_models.NetworkConfig(
                wifi=api_models.WiFiConfig(ssid="default", password="default"),
                thread=api_models.ThreadExternalConfig(operational_dataset_hex="default")
            ),
            dut_config=api_models.DutConfig(
                pairing_mode=api_models.DutPairingModeEnum.BLE_WIFI,
                setup_code="20202021",
                discriminator="3840",
                trace_log=False
            )
        )
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config
        mock_sync_apis.projects_api.create_project_api_v1_projects_post.return_value = sample_project

        with patch("th_cli.commands.project.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(project, ["create", "--name", "Test Project"])

        # Assert
        assert result.exit_code == 0
        assert "Project 'Test Project' created with ID 1" in result.output
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.assert_called_once()
        mock_sync_apis.projects_api.create_project_api_v1_projects_post.assert_called_once()
        mock_api_client.close.assert_called_once()

    def test_create_project_success_with_custom_config(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        mock_project_config: Path
    ) -> None:
        """Test successful project creation with custom configuration file."""
        # Arrange
        default_config = api_models.TestEnvironmentConfig(
            network=api_models.NetworkConfig(
                wifi=api_models.WiFiConfig(ssid="default", password="default"),
                thread=api_models.ThreadExternalConfig(operational_dataset_hex="default")
            ),
            dut_config=api_models.DutConfig(
                pairing_mode=api_models.DutPairingModeEnum.BLE_WIFI,
                setup_code="20202021",
                discriminator="3840",
                trace_log=False
            )
        )
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config
        mock_sync_apis.projects_api.create_project_api_v1_projects_post.return_value = sample_project

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(
                project, ["create", "--name", "Test Project", "--config", str(mock_project_config)]
            )

        # Assert
        assert result.exit_code == 0
        assert "Project 'Test Project' created with ID 1" in result.output

    def test_create_project_config_file_not_found(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project creation with non-existent config file."""
        # Arrange
        default_config = api_models.TestEnvironmentConfig(
            network=api_models.NetworkConfig(
                wifi=api_models.WiFiConfig(ssid="default", password="default"),
                thread=api_models.ThreadExternalConfig(operational_dataset_hex="default")
            ),
            dut_config=api_models.DutConfig(
                pairing_mode=api_models.DutPairingModeEnum.BLE_WIFI,
                setup_code="20202021",
                discriminator="3840",
                trace_log=False
            )
        )
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["create", "--name", "Test Project", "--config", "nonexistent.json"])

        # Assert
        assert result.exit_code == 1
        assert "File not found: nonexistent.json" in result.output

    def test_create_project_invalid_json_config(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        temp_dir: Path
    ) -> None:
        """Test project creation with invalid JSON in config file."""
        # Arrange
        invalid_config_file = temp_dir / "invalid.json"
        invalid_config_file.write_text("{ invalid json content")

        default_config = api_models.TestEnvironmentConfig(
            network=api_models.NetworkConfig(
                wifi=api_models.WiFiConfig(ssid="default", password="default"),
                thread=api_models.ThreadExternalConfig(operational_dataset_hex="default")
            ),
            dut_config=api_models.DutConfig(
                pairing_mode=api_models.DutPairingModeEnum.BLE_WIFI,
                setup_code="20202021",
                discriminator="3840",
                trace_log=False
            )
        )
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(
                project, ["create", "--name", "Test Project", "--config", str(invalid_config_file)]
            )

        # Assert
        assert result.exit_code == 1
        assert "Invalid JSON in config file" in result.output

    def test_create_project_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project creation with API error."""
        # Arrange
        default_config = api_models.TestEnvironmentConfig(
            network=api_models.NetworkConfig(
                wifi=api_models.WiFiConfig(ssid="default", password="default"),
                thread=api_models.ThreadExternalConfig(operational_dataset_hex="default")
            ),
            dut_config=api_models.DutConfig(
                pairing_mode=api_models.DutPairingModeEnum.BLE_WIFI,
                setup_code="20202021",
                discriminator="3840",
                trace_log=False
            )
        )
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config

        api_exception = UnexpectedResponse(
            status_code=400,
            reason_phrase="Bad Request",
            content=b"Bad Request",
            headers=Headers(),
        )
        mock_sync_apis.projects_api.create_project_api_v1_projects_post.side_effect = api_exception

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["create", "--name", "Test Project"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to create project 'Test Project' (Status: 400) - Bad Request" in result.output

    def test_create_project_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for create_project command."""
        # Act
        result = cli_runner.invoke(project, ["create", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "Create" in result.output
        assert "--name" in result.output
        assert "--config" in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestDeleteProjectCommand:
    """Test cases for the delete_project command."""

    def test_delete_project_success_with_yes_flag(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful project deletion with --yes flag."""
        # Arrange
        mock_sync_apis.projects_api.delete_project_api_v1_projects_id_delete.return_value = None

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["delete", "--id", "1", "--yes"])

        # Assert
        assert result.exit_code == 0
        assert "Project 1 was deleted." in result.output
        mock_sync_apis.projects_api.delete_project_api_v1_projects_id_delete.assert_called_once_with(id=1)

    def test_delete_project_success_with_confirmation(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful project deletion with user confirmation."""
        # Arrange
        mock_sync_apis.projects_api.delete_project_api_v1_projects_id_delete.return_value = None

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["delete", "--id", "1"], input="y\n")

        # Assert
        assert result.exit_code == 0
        assert "Project 1 was deleted." in result.output

    def test_delete_project_abort_on_no_confirmation(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project deletion aborted when user declines confirmation."""
        # Arrange
        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["delete", "--id", "1"], input="n\n")

        # Assert
        assert result.exit_code == 0  # Aborted
        assert "Operation cancelled." in result.output
        mock_sync_apis.projects_api.delete_project_api_v1_projects_id_delete.assert_not_called()

    def test_delete_project_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project deletion with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=404,
            reason_phrase="Not Found",
            content=b"Not Found",
            headers=Headers(),
        )
        mock_sync_apis.projects_api.delete_project_api_v1_projects_id_delete.side_effect = api_exception

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["delete", "--id", "1", "--yes"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to delete project ID '1' (Status: 404) - Not Found" in result.output

    def test_delete_project_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for delete_project command."""
        # Act
        result = cli_runner.invoke(project, ["delete", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "delete" in result.output
        assert "--id" in result.output
        assert "--yes" in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestListProjectsCommand:
    """Test cases for the list_projects command."""

    def test_list_projects_success_all_projects(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_projects: list[api_models.Project]
    ) -> None:
        """Test successful listing of all projects."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.return_value = sample_projects

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list"])

        # Assert
        assert result.exit_code == 0
        assert "ID" in result.output
        assert "Project Name" in result.output
        assert "Updated Time" in result.output
        for sample_project in sample_projects:
            assert str(sample_project.id) in result.output
            assert sample_project.name in result.output

    def test_list_projects_success_specific_project(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project
    ) -> None:
        """Test successful listing of a specific project by ID."""
        # Arrange
        mock_sync_apis.projects_api.read_project_api_v1_projects_id_get.return_value = sample_project

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert str(sample_project.id) in result.output
        assert sample_project.name in result.output
        mock_sync_apis.projects_api.read_project_api_v1_projects_id_get.assert_called_once_with(id=1)

    def test_list_projects_json_output(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_projects: list[api_models.Project]
    ) -> None:
        """Test listing projects with JSON output."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.return_value = sample_projects

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--json"])

        # Assert
        assert result.exit_code == 0
        # Should contain JSON formatted output
        assert '"id":' in result.output
        assert '"name":' in result.output

    def test_list_projects_with_pagination(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_projects: list[api_models.Project]
    ) -> None:
        """Test listing projects with pagination parameters."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.return_value = sample_projects[:2]

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--skip", "0", "--limit", "2"])

        # Assert
        assert result.exit_code == 0
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.assert_called_once_with(
            archived=False, skip=0, limit=2
        )

    def test_list_projects_archived(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_projects: list[api_models.Project]
    ) -> None:
        """Test listing archived projects."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.return_value = sample_projects

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--archived"])

        # Assert
        assert result.exit_code == 0
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.assert_called_once_with(
            archived=True, skip=None, limit=None
        )

    def test_list_projects_no_projects_found(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test listing projects when no projects are found."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.return_value = []

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Server did not return any project" in result.output

    def test_list_projects_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test listing projects with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=500,
            reason_phrase="Internal Server Error",
            content=b"Internal Server Error",
            headers=Headers(),
        )
        mock_sync_apis.projects_api.read_projects_api_v1_projects_get.side_effect = api_exception

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to list projects (Status: 500) - Internal Server Error" in result.output

    def test_list_projects_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for list_projects command."""
        # Act
        result = cli_runner.invoke(project, ["list", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "list" in result.output
        assert "--id" in result.output
        assert "--skip" in result.output
        assert "--limit" in result.output
        assert "--archived" in result.output
        assert "--json" in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestUpdateProjectCommand:
    """Test cases for the update_project command."""

    def test_update_project_success(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        mock_config: Path
    ) -> None:
        """Test successful project update."""
        # Arrange
        mock_sync_apis.projects_api.update_project_api_v1_projects_id_put.return_value = sample_project

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["update", "--id", "1", "--config", str(mock_config)])

        # Assert
        assert result.exit_code == 0
        assert "Project Test Project is updated with the new config." in result.output
        mock_sync_apis.projects_api.update_project_api_v1_projects_id_put.assert_called_once()

    def test_update_project_config_file_not_found(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project update with non-existent config file."""
        # Arrange
        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["update", "--id", "1", "--config", "nonexistent.json"])

        # Assert
        assert result.exit_code == 1
        assert "File not found: nonexistent.json" in result.output

    def test_update_project_invalid_json_config(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        temp_dir: Path
    ) -> None:
        """Test project update with invalid JSON in config file."""
        # Arrange
        invalid_config_file = temp_dir / "invalid.json"
        invalid_config_file.write_text("{ invalid json content")

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["update", "--id", "1", "--config", str(invalid_config_file)])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to parse JSON parameter" in result.output

    def test_update_project_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_config: Path
    ) -> None:
        """Test project update with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=404,
            reason_phrase="Not Found",
            content=b"Not Found",
            headers=Headers(),
        )
        mock_sync_apis.projects_api.update_project_api_v1_projects_id_put.side_effect = api_exception

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["update", "--id", "1", "--config", str(mock_config)])

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to update project with '1' (Status: 404) - Not Found" in result.output

    def test_update_project_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for update_project command."""
        # Act
        result = cli_runner.invoke(project, ["update", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "update" in result.output
        assert "--id" in result.output
        assert "--config" in result.output
