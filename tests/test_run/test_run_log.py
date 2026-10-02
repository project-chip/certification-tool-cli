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
"""Unit tests for th_cli/test_run/run_log.py."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import ResponseHandlingException
from th_cli.test_run import run_log
from th_cli.test_run.run_log import sync_log_file_from_backend


def _execution(state: api_models.TestStateEnum) -> Mock:
    execution = Mock()
    execution.state = state
    return execution


_LOG_BODY = (
    '{"level": "INFO", "timestamp": 1790000000.5, "message": "first", "test_suite_execution_index": null, '
    '"test_case_execution_index": null, "test_step_execution_index": null}\n'
    '{"level": "CHIPTOOL", "timestamp": 1790000001.5, "message": "second", "test_suite_execution_index": 0, '
    '"test_case_execution_index": 1, "test_step_execution_index": 2}\n'
)


def _apis(states: list[api_models.TestStateEnum], log: str = _LOG_BODY) -> Mock:
    apis = Mock()
    api = apis.test_run_executions_api
    api.read_test_run_execution_api_v1_test_run_executions__id__get = AsyncMock(
        side_effect=[_execution(s) for s in states]
    )
    api.download_log_api_v1_test_run_executions__id__log_get = AsyncMock(return_value=log)
    return apis


@pytest.mark.unit
class TestSyncLogFileFromBackend:
    @pytest.fixture(autouse=True)
    def no_sleep(self):
        with patch("th_cli.test_run.run_log.PERSIST_POLL_INTERVAL_S", 0):
            yield

    @pytest.mark.asyncio
    async def test_waits_for_persisted_terminal_state_then_replaces_log(self):
        apis = _apis(
            [
                api_models.TestStateEnum.executing,
                api_models.TestStateEnum.executing,
                api_models.TestStateEnum.passed,
            ]
        )
        with patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries") as mock_write:
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is True

        api = apis.test_run_executions_api
        assert api.read_test_run_execution_api_v1_test_run_executions__id__get.await_count == 3
        api.download_log_api_v1_test_run_executions__id__log_get.assert_awaited_once_with(
            id=5, json_entries=True, download=False
        )
        mock_write.assert_called_once()
        path, entries = mock_write.call_args.args
        assert path == "/logs/run.log"
        assert [(e.level, e.timestamp, e.message) for e in entries] == [
            ("INFO", 1790000000.5, "first"),
            ("CHIPTOOL", 1790000001.5, "second"),
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "state",
        [
            api_models.TestStateEnum.failed,
            api_models.TestStateEnum.error,
            api_models.TestStateEnum.cancelled,
            api_models.TestStateEnum.not_applicable,
        ],
    )
    async def test_any_terminal_state_counts_as_persisted(self, state):
        apis = _apis([state])
        with patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries") as mock_write:
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is True
        mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_pending_is_not_terminal(self):
        apis = _apis([api_models.TestStateEnum.pending, api_models.TestStateEnum.passed])
        with patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries"):
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is True
        assert apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions__id__get.await_count == 2

    @pytest.mark.asyncio
    async def test_times_out_and_keeps_local_file(self, capsys):
        apis = Mock()
        apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions__id__get = AsyncMock(
            return_value=_execution(api_models.TestStateEnum.executing)
        )
        with (
            patch.object(run_log, "PERSIST_TIMEOUT_S", 0),
            patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries") as mock_write,
        ):
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is False

        mock_write.assert_not_called()
        assert "Timed out" in capsys.readouterr().err

    @pytest.mark.asyncio
    async def test_api_error_keeps_local_file(self, capsys):
        apis = Mock()
        apis.test_run_executions_api.read_test_run_execution_api_v1_test_run_executions__id__get = AsyncMock(
            side_effect=ResponseHandlingException(Exception("connection refused"))
        )
        with patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries") as mock_write:
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is False

        mock_write.assert_not_called()
        assert "Could not fetch" in capsys.readouterr().err

    @pytest.mark.asyncio
    async def test_empty_backend_log_keeps_local_file(self):
        apis = _apis([api_models.TestStateEnum.passed], log="")
        with patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries") as mock_write:
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is False
        mock_write.assert_not_called()

    @pytest.mark.asyncio
    async def test_write_error_is_reported_not_raised(self, capsys):
        apis = _apis([api_models.TestStateEnum.passed])
        with patch(
            "th_cli.test_run.run_log.test_logging.write_log_file_from_entries", side_effect=PermissionError("denied")
        ):
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is False
        assert "Could not write" in capsys.readouterr().err

    @pytest.mark.asyncio
    async def test_malformed_backend_log_keeps_local_file(self, capsys):
        apis = _apis([api_models.TestStateEnum.passed], log='{"level": "INFO"}\nnot json\n')
        with patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries") as mock_write:
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is False
        mock_write.assert_not_called()
        assert "Could not parse" in capsys.readouterr().err

    @pytest.mark.asyncio
    async def test_blank_lines_are_skipped(self):
        apis = _apis([api_models.TestStateEnum.passed], log="\n" + _LOG_BODY + "\n\n")
        with patch("th_cli.test_run.run_log.test_logging.write_log_file_from_entries") as mock_write:
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is True
        assert len(mock_write.call_args.args[1]) == 2

    @pytest.mark.asyncio
    async def test_bad_timestamp_is_reported_not_raised(self, capsys):
        apis = _apis([api_models.TestStateEnum.passed])
        with patch(
            "th_cli.test_run.run_log.test_logging.write_log_file_from_entries", side_effect=ValueError("bad time")
        ):
            assert await sync_log_file_from_backend(apis, 5, "/logs/run.log") is False
        assert "Could not write" in capsys.readouterr().err
