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
"""Tests for the project commands (create, delete, list, update)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.project import project


@pytest.mark.unit
@pytest.mark.cli
class TestCreateProjectCommand:
    """Test cases for the create_project command."""

    def test_create_project_success_with_default_config(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_api_client: Mock, sample_project: api_models.Project
    ) -> None:
        """Test successful project creation with default configuration."""
        # Arrange
        default_config = {
            "network": {
                "wifi": {"ssid": "default", "password": "default"},
                "thread": {"operational_dataset_hex": "default"},
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": "3840",
                "trace_log": False,
            },
        }
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config
        mock_sync_apis.projects_api.create_project_api_v1_projects__post.return_value = sample_project

        with patch("th_cli.commands.project.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(project, ["create", "--name", "Test Project"])

        # Assert
        assert result.exit_code == 0
        assert "Project 'Test Project' created with ID 1" in result.output
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.assert_called_once()
        mock_sync_apis.projects_api.create_project_api_v1_projects__post.assert_called_once()
        mock_api_client.close.assert_called_once()

    def test_create_project_success_with_custom_config(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_project: api_models.Project, mock_project_config: Path
    ) -> None:
        """Test successful project creation with custom configuration file."""
        # Arrange
        default_config = {
            "network": {
                "wifi": {"ssid": "default", "password": "default"},
                "thread": {"operational_dataset_hex": "default"},
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": "3840",
                "trace_log": False,
            },
        }
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config
        mock_sync_apis.projects_api.create_project_api_v1_projects__post.return_value = sample_project

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
        default_config = {
            "network": {
                "wifi": {"ssid": "default", "password": "default"},
                "thread": {"operational_dataset_hex": "default"},
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": "3840",
                "trace_log": False,
            },
        }
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["create", "--name", "Test Project", "--config", "nonexistent.json"])

        # Assert
        assert result.exit_code == 1
        assert "File not found: nonexistent.json" in result.output

    def test_create_project_invalid_json_config(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, temp_dir: Path
    ) -> None:
        """Test project creation with invalid JSON in config file."""
        # Arrange
        invalid_config_file = temp_dir / "invalid.json"
        invalid_config_file.write_text("{ invalid json content")

        default_config = {
            "network": {
                "wifi": {"ssid": "default", "password": "default"},
                "thread": {"operational_dataset_hex": "default"},
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": "3840",
                "trace_log": False,
            },
        }
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
        default_config = {
            "network": {
                "wifi": {"ssid": "default", "password": "default"},
                "thread": {"operational_dataset_hex": "default"},
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": "3840",
                "trace_log": False,
            },
        }
        mock_sync_apis.projects_api.default_config_api_v1_projects_default_config_get.return_value = default_config

        api_exception = UnexpectedResponse(
            status_code=400,
            content=b"Bad Request",
        )
        mock_sync_apis.projects_api.create_project_api_v1_projects__post.side_effect = api_exception

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
        mock_sync_apis.projects_api.delete_project_api_v1_projects__id__delete.return_value = None

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["delete", "--id", "1", "--yes"])

        # Assert
        assert result.exit_code == 0
        assert "Project 1 was deleted." in result.output
        mock_sync_apis.projects_api.delete_project_api_v1_projects__id__delete.assert_called_once_with(id=1)

    def test_delete_project_success_with_confirmation(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test successful project deletion with user confirmation."""
        # Arrange
        mock_sync_apis.projects_api.delete_project_api_v1_projects__id__delete.return_value = None

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
        mock_sync_apis.projects_api.delete_project_api_v1_projects__id__delete.assert_not_called()

    def test_delete_project_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project deletion with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=404,
            content=b"Not Found",
        )
        mock_sync_apis.projects_api.delete_project_api_v1_projects__id__delete.side_effect = api_exception

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
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_projects: list[api_models.Project]
    ) -> None:
        """Test successful listing of all projects."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.return_value = sample_projects

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
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_project: api_models.Project
    ) -> None:
        """Test successful listing of a specific project by ID."""
        # Arrange
        mock_sync_apis.projects_api.read_project_api_v1_projects__id__get.return_value = sample_project

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert str(sample_project.id) in result.output
        assert sample_project.name in result.output
        mock_sync_apis.projects_api.read_project_api_v1_projects__id__get.assert_called_once_with(id=1)

    def test_list_projects_json_output(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_projects: list[api_models.Project]
    ) -> None:
        """Test listing projects with JSON output."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.return_value = sample_projects

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--json"])

        # Assert
        assert result.exit_code == 0
        # Should contain JSON formatted output
        assert '"id":' in result.output
        assert '"name":' in result.output

    def test_list_projects_with_pagination(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_projects: list[api_models.Project]
    ) -> None:
        """Test listing projects with pagination parameters."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.return_value = sample_projects[:2]

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--skip", "0", "--limit", "2"])

        # Assert
        assert result.exit_code == 0
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.assert_called_once_with(
            archived=False, skip=0, limit=2
        )

    def test_list_projects_archived(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_projects: list[api_models.Project]
    ) -> None:
        """Test listing archived projects."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.return_value = sample_projects

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["list", "--archived"])

        # Assert
        assert result.exit_code == 0
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.assert_called_once_with(
            archived=True, skip=None, limit=None
        )

    def test_list_projects_no_projects_found(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test listing projects when no projects are found."""
        # Arrange
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.return_value = []

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
            content=b"Internal Server Error",
        )
        mock_sync_apis.projects_api.read_projects_api_v1_projects__get.side_effect = api_exception

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
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_project: api_models.Project, mock_config: Path
    ) -> None:
        """Test successful project update."""
        # Arrange
        mock_sync_apis.projects_api.read_project_api_v1_projects__id__get.return_value = sample_project
        mock_sync_apis.projects_api.update_project_api_v1_projects__id__put.return_value = sample_project

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["update", "--id", "1", "--config", str(mock_config)])

        # Assert
        assert result.exit_code == 0
        assert "Project 'Test Project' was updated." in result.output
        mock_sync_apis.projects_api.update_project_api_v1_projects__id__put.assert_called_once()

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
        self, cli_runner: CliRunner, mock_sync_apis: Mock, temp_dir: Path
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
        self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_config: Path, sample_project: api_models.Project
    ) -> None:
        """Test project update with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=404,
            content=b"Not Found",
        )
        mock_sync_apis.projects_api.read_project_api_v1_projects__id__get.return_value = sample_project
        mock_sync_apis.projects_api.update_project_api_v1_projects__id__put.side_effect = api_exception

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


@pytest.mark.unit
@pytest.mark.cli
class TestExportProjectCommand:
    """Test cases for the project export command."""

    def test_export_project_success_default_filename(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        temp_dir: Path,
    ) -> None:
        """Test successful project export with auto-generated filename."""
        # Arrange
        project_create = api_models.ProjectCreate(
            name="Test Project",
            config=sample_project.config,
            pics=api_models.PICS(clusters={}),
        )
        mock_sync_apis.projects_api.export_project_config_api_v1_projects__id__export_get.return_value = (
            project_create
        )

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            with cli_runner.isolated_filesystem(temp_dir=temp_dir):
                # Act
                result = cli_runner.invoke(project, ["export", "--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert "exported to" in result.output
        mock_sync_apis.projects_api.export_project_config_api_v1_projects__id__export_get.assert_called_once_with(id=1)

    def test_export_project_success_custom_filename(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        temp_dir: Path,
    ) -> None:
        """Test successful project export to a specified output file."""
        # Arrange
        project_create = api_models.ProjectCreate(
            name="Test Project",
            config=sample_project.config,
            pics=api_models.PICS(clusters={}),
        )
        mock_sync_apis.projects_api.export_project_config_api_v1_projects__id__export_get.return_value = (
            project_create
        )
        output_path = str(temp_dir / "my_export.json")

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(project, ["export", "--id", "1", "--output-file", output_path])

        # Assert
        assert result.exit_code == 0
        assert f"exported to '{output_path}'" in result.output
        assert Path(output_path).exists()
        saved = json.loads(Path(output_path).read_text())
        assert saved["name"] == "Test Project"

    def test_export_project_file_content_is_valid_json(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        temp_dir: Path,
    ) -> None:
        """Test that the exported file contains valid JSON matching the project config."""
        # Arrange
        project_create = api_models.ProjectCreate(
            name="My Device",
            config=sample_project.config,
            pics=api_models.PICS(clusters={}),
        )
        mock_sync_apis.projects_api.export_project_config_api_v1_projects__id__export_get.return_value = (
            project_create
        )
        output_path = str(temp_dir / "export.json")

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(project, ["export", "--id", "42", "--output-file", output_path])

        assert result.exit_code == 0
        data = json.loads(Path(output_path).read_text())
        assert data["name"] == "My Device"
        assert "config" in data

    def test_export_project_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project export with API error."""
        # Arrange
        mock_sync_apis.projects_api.export_project_config_api_v1_projects__id__export_get.side_effect = (
            UnexpectedResponse(status_code=404, content=b"Not Found")
        )

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(project, ["export", "--id", "99"])

        assert result.exit_code == 1
        assert "Error: Failed to export project ID '99' (Status: 404) - Not Found" in result.output

    def test_export_project_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the export command."""
        result = cli_runner.invoke(project, ["export", "--help"])

        assert result.exit_code == 0
        assert "--id" in result.output
        assert "--output-file" in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestImportProjectCommand:
    """Test cases for the project import command."""

    def test_import_project_success(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        temp_dir: Path,
    ) -> None:
        """Test successful project import from a JSON file."""
        # Arrange
        import_file = temp_dir / "import.json"
        import_file.write_text(
            json.dumps({"name": "Imported Project", "config": sample_project.config, "pics": {"clusters": {}}})
        )
        mock_sync_apis.projects_api.importproject_config_api_v1_projects_import_post.return_value = sample_project

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(project, ["import", "--file", str(import_file)])

        # Assert
        assert result.exit_code == 0
        assert f"Project '{sample_project.name}' imported with ID {sample_project.id}" in result.output
        mock_sync_apis.projects_api.importproject_config_api_v1_projects_import_post.assert_called_once()

    def test_import_project_file_not_found(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test project import with a non-existent file (Click validates exists=True)."""
        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(project, ["import", "--file", "nonexistent.json"])

        assert result.exit_code == 2
        assert "does not exist" in result.output

    def test_import_project_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        temp_dir: Path,
    ) -> None:
        """Test project import with API error."""
        # Arrange
        import_file = temp_dir / "import.json"
        import_file.write_text(
            json.dumps({"name": "Imported Project", "config": sample_project.config, "pics": {"clusters": {}}})
        )
        mock_sync_apis.projects_api.importproject_config_api_v1_projects_import_post.side_effect = (
            UnexpectedResponse(status_code=422, content=b"Unprocessable Entity")
        )

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            result = cli_runner.invoke(project, ["import", "--file", str(import_file)])

        assert result.exit_code == 1
        assert "422" in result.output

    def test_import_project_passes_file_bytes_to_api(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_project: api_models.Project,
        temp_dir: Path,
    ) -> None:
        """Test that the import command sends the file bytes to the API correctly."""
        # Arrange
        payload = {"name": "Byte Check Project", "config": sample_project.config, "pics": {"clusters": {}}}
        import_file = temp_dir / "import.json"
        import_file.write_text(json.dumps(payload))
        mock_sync_apis.projects_api.importproject_config_api_v1_projects_import_post.return_value = sample_project

        with patch("th_cli.commands.project.SyncApis", return_value=mock_sync_apis):
            cli_runner.invoke(project, ["import", "--file", str(import_file)])

        call_args = mock_sync_apis.projects_api.importproject_config_api_v1_projects_import_post.call_args
        body = call_args.kwargs["body"]
        assert body.import_file == import_file.read_bytes()

    def test_import_project_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the import command."""
        result = cli_runner.invoke(project, ["import", "--help"])

        assert result.exit_code == 0
        assert "--file" in result.output
