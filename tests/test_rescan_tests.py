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
"""Tests for the rescan_tests command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.rescan_tests import rescan_tests
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestRescanTestsCommand:
    """Test cases for the rescan_tests command."""

    def test_rescan_tests_success(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        """Test successful rescan of test collections."""
        # Arrange
        api = mock_sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post
        api.return_value = sample_test_collections

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(rescan_tests)

        # Assert
        assert result.exit_code == 0
        assert "Rescanned test collections successfully" in result.output
        api.assert_called_once()
        mock_api_client.close.assert_called_once()

    def test_rescan_tests_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test rescan_tests with configuration error."""
        with patch(
            "th_cli.commands.rescan_tests.get_client", side_effect=ConfigurationError("Could not connect to server")
        ):
            result = cli_runner.invoke(rescan_tests)

        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_rescan_tests_api_error(self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_api_client: Mock) -> None:
        """Test rescan_tests when the server reports the Test Engine is busy."""
        api_exception = UnexpectedResponse(
            status_code=409,
            content=b"Test Engine is busy.",
        )
        api = mock_sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post
        api.side_effect = api_exception

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(rescan_tests)

        assert result.exit_code == 1
        assert "Error: Failed to rescan test collections (Status: 409) - Test Engine is busy." in result.output
        mock_api_client.close.assert_called_once()

    def test_rescan_tests_generic_exception(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_api_client: Mock
    ) -> None:
        """Test rescan_tests with an unexpected error."""
        api = mock_sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post
        api.side_effect = Exception("Unexpected error")

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(rescan_tests)

        assert result.exit_code == 1
        assert "Could not rescan test collections" in result.output
        mock_api_client.close.assert_called_once()

    def test_rescan_tests_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for the rescan_tests command."""
        result = cli_runner.invoke(rescan_tests, ["--help"])

        assert result.exit_code == 0
        assert "Re-run test collection discovery on the backend" in result.output
