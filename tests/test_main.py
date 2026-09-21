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
"""Tests for the th-cli root group and its --version handling.

Regression tests for #1005: th-cli used to call GET /api/v1/version on every
invocation (not just --version) because click.version_option's `message` was
evaluated eagerly at decoration/import time.
"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from th_cli.main import root


@pytest.mark.unit
@pytest.mark.cli
class TestRootVersionOption:
    """Test cases for th-cli's --version handling."""

    def test_help_does_not_query_server_version(self, cli_runner: CliRunner) -> None:
        """--help (and, by extension, any other invocation) must not hit the backend."""
        with patch("th_cli.main.get_versions") as mock_get_versions:
            result = cli_runner.invoke(root, ["--help"])

        assert result.exit_code == 0
        mock_get_versions.assert_not_called()

    def test_no_args_does_not_query_server_version(self, cli_runner: CliRunner) -> None:
        """Invoking the CLI with no subcommand must not hit the backend either."""
        with patch("th_cli.main.get_versions") as mock_get_versions:
            cli_runner.invoke(root, [])

        mock_get_versions.assert_not_called()

    def test_version_queries_server_version(self, cli_runner: CliRunner) -> None:
        """--version is the only invocation expected to reach out to the backend."""
        with patch("th_cli.main.get_versions", return_value={"Backend Version": "1.0.0"}) as mock_get_versions:
            result = cli_runner.invoke(root, ["--version"])

        assert result.exit_code == 0
        mock_get_versions.assert_called_once()
        assert "Backend Version" in result.output

    def test_version_exits_cleanly_when_server_unreachable(self, cli_runner: CliRunner) -> None:
        """--version must still print CLI-only info and exit 0 if the backend call fails."""
        with patch("th_cli.main.get_versions", side_effect=Mock(side_effect=Exception("unreachable"))):
            result = cli_runner.invoke(root, ["--version"])

        assert result.exit_code == 0
        assert "Not able to retrieve versions from server." in result.output
