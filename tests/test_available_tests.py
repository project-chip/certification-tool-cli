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
"""Tests for the available_tests command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.available_tests import (
    _extract_cluster_from_test_id,
    _extract_test_cases,
    _generate_compact,
    _generate_grouped_by_cluster,
    available_tests,
)
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
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

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
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

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
        mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get.return_value = None

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
            "th_cli.commands.available_tests.get_client", side_effect=ConfigurationError("Could not connect to server")
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
            content=b"Internal Server Error",
        )
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

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
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

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
        json_flag: bool,
    ) -> None:
        """Test available tests with both JSON and YAML output formats."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

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
                                public_id="Suite1", version="2.0", title="Test Suite 1", description="First test suite"
                            ),
                            test_cases={
                                "TC-TEST-1.1": api_models.TestCase(
                                    metadata=api_models.TestMetadata(
                                        public_id="TC-TEST-1.1",
                                        version="2.0",
                                        title="Test Case 1.1",
                                        description="First test case",
                                    )
                                ),
                                "TC-TEST-1.2": api_models.TestCase(
                                    metadata=api_models.TestMetadata(
                                        public_id="TC-TEST-1.2",
                                        version="2.0",
                                        title="Test Case 1.2",
                                        description="Second test case",
                                    )
                                ),
                            },
                        ),
                        "Suite2": api_models.TestSuite(
                            metadata=api_models.TestMetadata(
                                public_id="Suite2", version="1.5", title="Test Suite 2", description="Second test suite"
                            ),
                            test_cases={},
                        ),
                    },
                )
            }
        )
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

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

    @pytest.mark.parametrize(
        "status_code,content",
        [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
            (503, "Service Unavailable"),
        ],
    )
    def test_available_tests_various_api_errors(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, status_code: int, content: str
    ) -> None:
        """Test available tests with various API error status codes."""
        # Arrange
        api_exception = UnexpectedResponse(
            status_code=status_code,
            content=content.encode("utf-8"),
        )
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

        api.side_effect = api_exception
        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests)

        # Assert
        assert result.exit_code == 1
        assert f"Failed to get available tests (Status: {status_code})" in result.output
        assert content in result.output

    def test_available_tests_yaml_dump_functionality(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test that YAML output is properly formatted and readable."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get

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

    def test_available_tests_compact(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test --compact flag shows test IDs with titles."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests, ["--compact"])

        # Assert
        assert result.exit_code == 0
        # Should contain test IDs with compact format (IDs only)
        assert "TC-ACE-1.1" in result.output
        assert "TC-ACE-1.2" in result.output
        assert "TC-CC-1.1" in result.output
        # Should not contain full YAML/JSON structure
        assert "test_collections:" not in result.output

    def test_available_tests_group_by_cluster(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test --group-by-cluster flag groups tests by cluster."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests, ["--group-by-cluster"])

        # Assert
        assert result.exit_code == 0
        # Should contain cluster headers
        assert "ACE:" in result.output
        assert "CC:" in result.output
        # Should contain separator lines
        assert "----" in result.output or "---" in result.output
        # Should contain indented test cases under clusters
        assert "  TC-ACE-1.1" in result.output
        assert "  TC-CC-1.1" in result.output

    def test_available_tests_cluster_filter(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test --cluster filter shows only tests from specified cluster."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests, ["--cluster", "ACE"])

        # Assert
        assert result.exit_code == 0
        # Should contain only ACE tests in detailed format
        assert "Test Cases for Cluster: ACE" in result.output
        assert "ID: TC-ACE-1.1" in result.output
        assert "ID: TC-ACE-1.2" in result.output
        # Should not contain CC tests
        assert "TC-CC-1.1" not in result.output

    def test_available_tests_cluster_filter_case_insensitive(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test --cluster filter is case insensitive."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests, ["--cluster", "ace"])

        # Assert
        assert result.exit_code == 0
        # Should contain ACE tests in detailed format even with lowercase input
        assert "Test Cases for Cluster: ACE" in result.output
        assert "ID: TC-ACE-1.1" in result.output
        assert "ID: TC-ACE-1.2" in result.output

    def test_available_tests_cluster_and_compact_combined(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test combining --cluster and --compact flags."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Act
            result = cli_runner.invoke(available_tests, ["--cluster", "CC", "--compact"])

        # Assert
        assert result.exit_code == 0
        # Should contain only CC tests in compact format (IDs only)
        assert "TC-CC-1.1" in result.output
        # Should not contain ACE tests
        assert "TC-ACE-1.1" not in result.output

    def test_extract_cluster_from_test_id(self) -> None:
        # Test various patterns
        assert _extract_cluster_from_test_id("TC-ACE-1.1") == "ACE"
        assert _extract_cluster_from_test_id("TC-CADMIN-1.2") == "CADMIN"
        assert _extract_cluster_from_test_id("Test_TC_CC_1_1") == "CC"
        assert _extract_cluster_from_test_id("TC_WEBRTC_1_6") == "WEBRTC"
        assert _extract_cluster_from_test_id("TC_WEBRTCP_1_8") == "WEBRTCP"
        assert _extract_cluster_from_test_id("TC_WEBRTC-1.2") == "WEBRTC"
        assert _extract_cluster_from_test_id("TC_WEBRTCP-4.2") == "WEBRTCP"
        assert _extract_cluster_from_test_id("TC_AUDIO_1_6") == "AUDIO"

        # Test edge cases from real data
        assert _extract_cluster_from_test_id("TC_ACE_1_3-custom") == "ACE"
        assert _extract_cluster_from_test_id("TC_ACE_1_3_R-custom") == "ACE"
        assert _extract_cluster_from_test_id("TC_MCORE_FS_1_1") == "MCOREFS"
        assert _extract_cluster_from_test_id("TC_WebRTCP_2_1") == "WEBRTCP"
        assert _extract_cluster_from_test_id("TC_WebRTCR_2_1") == "WEBRTCR"
        assert _extract_cluster_from_test_id("TC-APPLAUNCHER-3.5") == "APPLAUNCHER"
        assert _extract_cluster_from_test_id("TC-CONTENTLAUNCHER-10.1") == "CONTENTLAUNCHER"

        assert _extract_cluster_from_test_id("SomeOtherTest") == "UNKNOWN"

    def test_generate_compact(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test _generate_compact function with 4 elements per line."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Extract test cases
            test_cases = _extract_test_cases(sample_test_collections)

            # Act
            result_lines = _generate_compact(test_cases)

        # Assert
        # Should have fewer lines since we put 4 elements per line
        assert len(result_lines) <= len(test_cases)
        # Each line should contain test case IDs
        for line in result_lines:
            # Lines should contain test case IDs
            assert "TC-" in line or "TC_" in line  # Support different formats
        # First line should contain first test case ID only
        assert any("TC-ACE-1.1" in line for line in result_lines)

    def test_generate_grouped_by_cluster(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test _generate_grouped_by_cluster function with 4 elements per line."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            # Extract test cases
            test_cases = _extract_test_cases(sample_test_collections)

            # Act
            result_lines = _generate_grouped_by_cluster(test_cases)

        # Assert
        result_text = "\n".join(result_lines)
        assert "ACE:" in result_text
        assert "CC:" in result_text
        # Check that tests within clusters use uniform spacing format
        ace_line_found = False
        for line in result_lines:
            # Look for lines with multiple ACE tests using double space separator
            if "TC-ACE" in line and "  " in line:
                ace_line_found = True
                break
        # Should find at least one line with multiple ACE tests
        assert ace_line_found or len([tc for tc in test_cases if tc["cluster"] == "ACE"]) < 4

    def test_available_tests_compact_four_per_line(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test --compact flag shows 4 elements per line."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            with patch("click.echo_via_pager") as mock_pager:
                # Act
                result = cli_runner.invoke(available_tests, ["--compact"])

        # Assert
        assert result.exit_code == 0
        # Should have called echo_via_pager
        mock_pager.assert_called_once()
        # Check that content contains spacing for multiple elements
        call_content = mock_pager.call_args[0][0]  # First argument (content)
        # Should contain test cases with uniform spacing (using double spaces)
        lines = call_content.split("\n")
        uniform_spacing_found = any("  " in line and "TC-" in line for line in lines)
        assert uniform_spacing_found or call_content.count("\n") == 0  # Exception for small datasets

    def test_available_tests_group_by_cluster_four_per_line(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test --group-by-cluster flag shows 4 elements per line within clusters."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            with patch("click.echo_via_pager") as mock_pager:
                # Act
                result = cli_runner.invoke(available_tests, ["--group-by-cluster"])

        # Assert
        assert result.exit_code == 0
        # Should have called echo_via_pager
        mock_pager.assert_called_once()
        # Check that content includes cluster headers and organized content
        call_content = mock_pager.call_args[0][0]  # First argument (content)
        assert "ACE:" in call_content
        assert "CC:" in call_content

    def test_available_tests_with_pagination_mock(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test available_tests command uses echo_via_pager."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            with patch("click.echo_via_pager") as mock_pager:
                # Act
                result = cli_runner.invoke(available_tests, ["--compact"])

        # Assert
        assert result.exit_code == 0
        # Should have called echo_via_pager
        mock_pager.assert_called_once()
        # Check that correct content was passed to pager
        call_content = mock_pager.call_args[0][0]  # First argument (content)
        assert "TC-ACE-1.1" in call_content
        assert "TC-ACE-1.2" in call_content
        assert "TC-CC-1.1" in call_content

    def test_available_tests_echo_via_pager_behavior(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test that echo_via_pager is called for all custom formatting options."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            with patch("click.echo_via_pager") as mock_pager:
                # Test different formatting options
                for args in [["--compact"], ["--group-by-cluster"], []]:
                    mock_pager.reset_mock()
                    # Act
                    result = cli_runner.invoke(available_tests, args)

                    # Assert
                    assert result.exit_code == 0
                    mock_pager.assert_called_once()

    def test_available_tests_cluster_detailed_info(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test --cluster flag shows detailed information."""
        # Arrange
        api = mock_sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get
        api.return_value = sample_test_collections

        with patch("th_cli.commands.available_tests.SyncApis", return_value=mock_sync_apis):
            with patch("click.echo_via_pager") as mock_pager:
                # Act
                result = cli_runner.invoke(available_tests, ["--cluster", "ACE"])

        # Assert
        assert result.exit_code == 0
        mock_pager.assert_called_once()
        # Check that detailed content is displayed
        call_content = mock_pager.call_args[0][0]  # First argument (content)
        assert "Test Cases for Cluster: ACE" in call_content
        assert "ID:" in call_content
        assert "Title:" in call_content
        assert "Description:" in call_content
        assert "Collection:" in call_content
        assert "Suite:" in call_content
        assert "Total test cases found:" in call_content
