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
"""Tests for response handling in the generated ApiClient.

These go through the real ApiClient, with an httpx mock transport standing in for the
backend, so they exercise ApiClient.send() rather than mocking the generated API methods.
"""

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from click.testing import CliRunner

from th_cli.api_lib_autogen.api_client import ApiClient, SyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.commands.test_run_execution import test_run_execution

LOG_TEXT = (
    "INFO       | 2026-10-01 20:25:37.092667 | Run Test Runner is Ready\n"
    "INFO       | 2026-10-01 20:25:50.817567 | Test Suite Completed [PASSED]\n"
    "INFO       | 2026-10-01 20:25:50.820625 | Test Run Completed [PASSED]\n"
)


def _client_for(
    status_code: int,
    content: bytes = b"",
    content_type: str = "text/plain; charset=utf-8",
    requests: list[httpx.Request] | None = None,
) -> ApiClient:
    """An ApiClient whose requests are all answered with the given fixed response."""

    def handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        return httpx.Response(status_code, content=content, headers={"content-type": content_type})

    return ApiClient(host="http://th.test", transport=httpx.MockTransport(handler))


@pytest.mark.unit
class TestApiClientSend:
    """ApiClient.send() response handling, by declared return type and status code."""

    def test_untyped_text_response_returns_body(self) -> None:
        # Endpoints whose OpenAPI schema declares no response content (e.g. the plain-text
        # test run log) are generated with type_=None; their body must not be discarded.
        client = _client_for(200, LOG_TEXT.encode("utf-8"))

        result = client.request_sync(type_=None, method="GET", url="/api/v1/test_run_executions/50/log")

        assert result == LOG_TEXT

    def test_no_content_returns_none(self) -> None:
        client = _client_for(204)

        assert client.request_sync(type_=None, method="DELETE", url="/api/v1/thing") is None

    def test_bytes_response_returns_raw_content(self) -> None:
        client = _client_for(200, b"PK\x03\x04zip", content_type="application/zip")

        assert client.request_sync(type_=bytes, method="GET", url="/api/v1/thing") == b"PK\x03\x04zip"

    def test_json_response_is_validated_to_type(self) -> None:
        client = _client_for(200, b'{"a": 1}', content_type="application/json")

        assert client.request_sync(type_=dict[str, int], method="GET", url="/api/v1/thing") == {"a": 1}

    def test_error_status_raises_unexpected_response(self) -> None:
        client = _client_for(404, b"Not found")

        with pytest.raises(UnexpectedResponse):
            client.request_sync(type_=None, method="GET", url="/api/v1/thing")

    def test_generated_download_log_returns_log_text(self) -> None:
        requests: list[httpx.Request] = []
        apis = SyncApis(_client_for(200, LOG_TEXT.encode("utf-8"), requests=requests))

        result = apis.test_run_executions_api.download_log_api_v1_test_run_executions__id__log_get(
            id=50, json_entries=False, download=False
        )

        assert result == LOG_TEXT
        assert requests[0].url.path == "/api/v1/test_run_executions/50/log"


@pytest.mark.unit
@pytest.mark.cli
class TestTestRunExecutionLogThroughApiClient:
    """`test-run-execution log` against a text/plain backend response, without mocking the API."""

    def test_log_prints_plain_text_log(self, cli_runner: CliRunner) -> None:
        client = _client_for(200, LOG_TEXT.encode("utf-8"))

        with patch("th_cli.commands.test_run_execution.get_client", return_value=client):
            result = cli_runner.invoke(test_run_execution, ["log", "--id", "50"])

        assert result.exit_code == 0, result.output
        assert "Run Test Runner is Ready" in result.output
        assert "Test Run Completed [PASSED]" in result.output
        assert "No log content available" not in result.output

    def test_log_writes_plain_text_log_to_file(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        client = _client_for(200, LOG_TEXT.encode("utf-8"))
        output_file = tmp_path / "run.log"

        with patch("th_cli.commands.test_run_execution.get_client", return_value=client):
            result = cli_runner.invoke(test_run_execution, ["log", "--id", "50", "--output-file", str(output_file)])

        assert result.exit_code == 0, result.output
        assert output_file.read_text(encoding="utf-8") == LOG_TEXT

    def test_log_reports_empty_log(self, cli_runner: CliRunner) -> None:
        client = _client_for(200, b"")

        with patch("th_cli.commands.test_run_execution.get_client", return_value=client):
            result = cli_runner.invoke(test_run_execution, ["log", "--id", "50"])

        assert result.exit_code == 0, result.output
        assert "No log content available" in result.output
