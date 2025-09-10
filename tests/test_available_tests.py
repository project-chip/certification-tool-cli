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
"""Tests for the available_tests command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from httpx import Headers

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.available_tests import available_tests
from th_cli.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.cli
class TestAvailableTestsCommand:
    """Test cases for the available_tests command."""

    def test_available_tests_success_yaml_output(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        """Test successful available tests retrieval with YAML output (default)."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.return_value = sample_test_collections
        with patch("th_cli.commands.available_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 0
        # Should contain YAML formatted output (not JSON)
        assert "SDK YAML Tests:" in result.output
        assert "FirstChipToolSuite:" in result.output
        assert "TC-ACE-1.1:" in result.output
        api.assert_called_once()
        mock_api_client.close.assert_called_once()

    def test_available_tests_success_json_output(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        """Test successful available tests retrieval with JSON output."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.return_value = sample_test_collections
        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests, ["--json"])

        # Assert
        assert result.exit_code == 0
        # Should contain JSON formatted output
        assert '"test_collections"' in result.output
        assert '"SDK YAML Tests"' in result.output
        assert '"FirstChipToolSuite"' in result.output
        api.assert_called_once()

    def test_available_tests_empty_collections(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
    ) -> None:
        """Test handling of empty test collections."""
        # Arrange
        mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get.return_value = None

        with patch("th_cli.commands.available_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 1
        assert "Error: Server did not return test_collection" in result.output
        mock_api_client.close.assert_called_once()

    def test_available_tests_configuration_error(self, cli_runner: CliRunner) -> None:
        """Test available tests with configuration error."""
        # Arrange
        with patch(
            "th_cli.commands.available_tests.get_client",
            side_effect=ConfigurationError("Could not connect to server")
        ):
            # Act
            result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 1
        assert "Error: Could not connect to server" in result.output

    def test_available_tests_api_error(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
    ) -> None:
        """Test available tests with API error."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=500,
            reason_phrase="Internal Server Error",
            content=b"Internal Server Error",
            headers=Headers(),
        )
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.side_effect = api_exception
        with patch("th_cli.commands.available_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 1
        assert "Error: Failed to get available tests (Status: 500) - Internal Server Error" in result.output
        mock_api_client.close.assert_called_once()

    def test_available_tests_generic_exception(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
    ) -> None:
        """Test available tests with generic exception."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.side_effect = Exception("Network error")
        with patch("th_cli.commands.available_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 1
        assert "Could not fetch the available tests: Network error" in result.output
        assert "Please check if the API server is running and accessible" in result.output
        mock_api_client.close.assert_called_once()

    def test_available_tests_client_cleanup_on_exception(self, cli_runner: CliRunner, mock_api_client: Mock) -> None:
        """Test that client is properly cleaned up even when an exception occurs."""
        # Arrange
        with patch("th_cli.commands.available_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.available_tests.SyncApis", side_effect=Exception("API creation failed")):
                # Act
                result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 1
        mock_api_client.close.assert_called_once()

    def test_available_tests_help_message(self, cli_runner: CliRunner) -> None:
        """Test the help message for available_tests command."""
        # Act
        result = cli_runner.invoke(available_tests, ["--help"])

        # Assert
        assert result.exit_code == 0
        print(result.output)
        assert "available_tests" in result.output
        assert "Get a list of the available test" in result.output
        assert "--json" in result.output
        assert "Print JSON response for more details" in result.output

    @pytest.mark.parametrize("json_flag", [True, False])
    def test_available_tests_output_formats(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_test_collections: api_models.TestCollections,
        json_flag: bool
    ) -> None:
        """Test available tests with both JSON and YAML output formats."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.return_value = sample_test_collections
        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            args = ["--json"] if json_flag else []
            result = cli_runner.invoke(available_tests, args)

        # Assert
        assert result.exit_code == 0
        if json_flag:
            # JSON output should have quotes around keys
            assert '"test_collections"' in result.output
            assert '"SDK YAML Tests"' in result.output
        else:
            # YAML output should not have quotes around keys
            assert "test_collections:" in result.output
            assert "SDK YAML Tests:" in result.output

    def test_available_tests_complex_test_structure(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
    ) -> None:
        """Test available tests with complex test collection structure."""
        # Arrange
        complex_collections = api_models.TestCollections(
            test_collections={
                "Collection1": api_models.TestCollection(
                    name="Collection1",
                    path="/path/to/collection1",
                    test_suites={
                        "Suite1": api_models.TestSuite(
                            metadata=api_models.TestMetadata(
                                public_id="Suite1",
                                version="2.0",
                                title="Test Suite 1",
                                description="First test suite"
                            ),
                            test_cases={
                                "TC-TEST-1.1": api_models.TestCase(
                                    metadata=api_models.TestMetadata(
                                        public_id="TC-TEST-1.1",
                                        version="2.0",
                                        title="Test Case 1.1",
                                        description="First test case"
                                    )
                                ),
                                "TC-TEST-1.2": api_models.TestCase(
                                    metadata=api_models.TestMetadata(
                                        public_id="TC-TEST-1.2",
                                        version="2.0",
                                        title="Test Case 1.2",
                                        description="Second test case"
                                    )
                                )
                            }
                        ),
                        "Suite2": api_models.TestSuite(
                            metadata=api_models.TestMetadata(
                                public_id="Suite2",
                                version="1.5",
                                title="Test Suite 2",
                                description="Second test suite"
                            ),
                            test_cases={}
                        )
                    }
                )
            }
        )
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.return_value = complex_collections
        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 0
        assert "Collection1:" in result.output
        assert "Suite1:" in result.output
        assert "Suite2:" in result.output
        assert "TC-TEST-1.1:" in result.output
        assert "TC-TEST-1.2:" in result.output

    @pytest.mark.parametrize("status_code,content", [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (500, "Internal Server Error"),
        (503, "Service Unavailable")
    ])
    def test_available_tests_various_api_errors(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        status_code: int,
        content: str
    ) -> None:
        """Test available tests with various API error status codes."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=status_code,
            reason_phrase=content,
            content=content.encode('utf-8'),
            headers=Headers(),
        )
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.side_effect = api_exception
        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 1
        assert f"Failed to get available tests (Status: {status_code})" in result.output
        assert content in result.output

    def test_available_tests_yaml_dump_functionality(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test that YAML output is properly formatted and readable."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get

        api.return_value = sample_test_collections
        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 0
        # Check for YAML structure indicators
        assert "test_collections:" in result.output
        assert "  SDK YAML Tests:" in result.output or "SDK YAML Tests:" in result.output
        # Should not contain JSON-specific formatting
        assert '"test_collections":' not in result.output
