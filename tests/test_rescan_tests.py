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
from httpx import ConnectError, ReadTimeout

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import ResponseHandlingException, UnexpectedResponse
from th_cli.commands.rescan_tests import rescan_tests
from th_cli.exceptions import ConfigurationError


def _rescan_response(test_collections: api_models.TestCollections, **changes: object) -> api_models.TestCollections:
    changes_by_kind: dict[str, object] = {"added": [], "modified": [], "removed": [], "errors": []}
    changes_by_kind.update(changes)
    return api_models.TestCollections(
        test_collections=test_collections.test_collections,
        changes=api_models.RescanChanges(collections=list(test_collections.test_collections), **changes_by_kind),
    )


def _change(collection: str, test_case: str) -> api_models.TestCaseChange:
    return api_models.TestCaseChange(collection=collection, test_suite="suite", test_case=test_case)


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
        api.return_value = _rescan_response(sample_test_collections)

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                # Act
                result = cli_runner.invoke(rescan_tests)

        # Assert
        assert result.exit_code == 0
        assert "Rescanned test collections successfully" in result.output
        assert "No changes detected." in result.output
        api.assert_called_once()
        mock_api_client.close.assert_called_once()

    def _invoke(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        response: api_models.TestCollections,
    ) -> str:
        api = mock_sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post
        api.return_value = response

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(rescan_tests)

        assert result.exit_code == 0
        return result.output

    def test_rescan_tests_reports_changes_grouped_by_collection(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        """Added, modified and removed test cases are listed under their collection,
        and the collections without changes are summarized."""
        names = list(sample_test_collections.test_collections)
        changed, unchanged = names[0], names[1:]
        response = _rescan_response(
            sample_test_collections,
            added=[_change(changed, "TC-FAKE-1.1-custom")],
            modified=[_change(changed, "TC-ACE-1.3-custom")],
            removed=[_change(changed, "TC-OLD-1.1-custom")],
        )

        output = self._invoke(cli_runner, mock_sync_apis, mock_api_client, response)

        assert f"Rescanned test collections successfully ({len(names)} found)" in output
        assert "No changes detected" not in output
        lines = output.splitlines()
        assert changed in lines
        assert any(line.startswith("  + TC-FAKE-1.1-custom") and line.endswith("added") for line in lines)
        assert any(line.startswith("  ~ TC-ACE-1.3-custom") and line.endswith("modified") for line in lines)
        assert any(line.startswith("  - TC-OLD-1.1-custom") and line.endswith("removed") for line in lines)
        if unchanged:
            assert f"No changes in: {', '.join(unchanged)}" in output

    def test_rescan_tests_no_changes(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        output = self._invoke(cli_runner, mock_sync_apis, mock_api_client, _rescan_response(sample_test_collections))

        count = len(sample_test_collections.test_collections)
        assert f"Rescanned test collections successfully ({count} found). No changes detected." in output
        assert "Scripts that could not be parsed" not in output

    def test_rescan_tests_reports_parse_errors(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        """Scripts that failed to parse are listed with the reason, also when nothing else changed."""
        response = _rescan_response(
            sample_test_collections,
            errors=[
                api_models.ScriptError(script="TC_BAD_1_1.py", reason="Syntax error: invalid syntax (line 3)"),
                api_models.ScriptError(reason="Failed running command:\n  boom"),
            ],
        )

        output = self._invoke(cli_runner, mock_sync_apis, mock_api_client, response)

        assert "No changes detected." in output
        assert "Scripts that could not be parsed (skipped):" in output
        assert "  ! TC_BAD_1_1.py: Syntax error: invalid syntax (line 3)" in output
        assert "  ! Failed running command: boom" in output

    def test_rescan_tests_reports_custom_overrides(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        """Custom files overriding SDK modules are listed, separately from same-name copies nothing imports."""
        response = _rescan_response(
            sample_test_collections,
            custom_overrides=api_models.CustomOverrides(
                overriding=["TC_SUTestBase.py"], unused_copies=["TC_ACE_1_3.py"]
            ),
        )

        output = self._invoke(cli_runner, mock_sync_apis, mock_api_client, response)

        assert "No changes detected." in output
        assert "Custom files overriding SDK modules (used by every test that imports them):" in output
        assert "  ! TC_SUTestBase.py" in output
        assert "override nothing" in output
        assert "  - TC_ACE_1_3.py" in output

    def test_rescan_tests_no_custom_overrides_prints_nothing(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        response = _rescan_response(sample_test_collections, custom_overrides=api_models.CustomOverrides())

        output = self._invoke(cli_runner, mock_sync_apis, mock_api_client, response)

        assert "overriding SDK modules" not in output

    def test_rescan_tests_backend_without_change_report(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
        sample_test_collections: api_models.TestCollections,
    ) -> None:
        """A response without `changes` (older backend) falls back to the plain summary."""
        output = self._invoke(cli_runner, mock_sync_apis, mock_api_client, sample_test_collections)

        count = len(sample_test_collections.test_collections)
        assert f"Rescanned test collections successfully ({count} found)" in output
        assert "No changes detected" not in output

    def test_rescan_tests_no_response(
        self,
        cli_runner: CliRunner,
        mock_sync_apis: Mock,
        mock_api_client: Mock,
    ) -> None:
        """Test handling of a None response from the server."""
        api = mock_sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post
        api.return_value = None

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(rescan_tests)

        assert result.exit_code == 1
        assert "Error: Server did not return test_collections" in result.output
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

    def test_rescan_tests_timeout(self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_api_client: Mock) -> None:
        """A client-side timeout should not be reported as a failure: rescanning can
        outlast the CLI's timeout while the backend keeps running it to completion."""
        api = mock_sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post
        api.side_effect = ResponseHandlingException(ReadTimeout("timed out"))

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(rescan_tests)

        assert result.exit_code == 0
        assert "Rescan request sent (backend may still be processing)" in result.output
        mock_api_client.close.assert_called_once()

    def test_rescan_tests_response_handling_error_non_timeout(
        self, cli_runner: CliRunner, mock_sync_apis: Mock, mock_api_client: Mock
    ) -> None:
        """A non-timeout response-handling error should still be reported as a failure."""
        api = mock_sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post
        api.side_effect = ResponseHandlingException(ConnectError("connection refused"))

        with patch("th_cli.commands.rescan_tests.get_client", return_value=mock_api_client):
            with patch("th_cli.commands.rescan_tests.SyncApis", return_value=mock_sync_apis):
                result = cli_runner.invoke(rescan_tests)

        assert result.exit_code == 1
        assert "Could not rescan test collections" in result.output
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
        # Click wraps the help text at a terminal-width-dependent column, so
        # collapse whitespace/newlines before checking for the substring —
        # otherwise the wrap point can land inside the expected text.
        normalized_output = " ".join(result.output.split())
        assert "Re-run test collection discovery on the backend" in normalized_output
