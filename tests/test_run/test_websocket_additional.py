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
"""Additional coverage tests for th_cli/test_run/websocket.py
uncovered branches: __log_test_run_update, __log_test_case_update
(browser-peer warning, step-error cleanup), __handle_incoming_socket_message,
__handle_test_update, __handle_log_record, __display_manual_pairing_code.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from th_cli.api_lib_autogen.models import (
    TestCaseExecution,
    TestCaseMetadata,
    TestRunExecutionWithChildren,
    TestStateEnum,
    TestStepExecution,
    TestSuiteExecution,
    TestSuiteMetadata,
)
from th_cli.shared_constants import MessageTypeEnum, TestStateEnum as SharedTestStateEnum
from th_cli.test_run.socket_schemas import (
    TestCaseUpdate,
    TestLogRecord,
    TestRunUpdate,
    TestStepUpdate,
    TestSuiteUpdate,
    TestUpdate,
    TimeOutNotification,
    UserResponseStatusEnum,
)
from th_cli.test_run.websocket import TestRunSocket

# ---------------------------------------------------------------------------
# Shared helpers (mirrors test_websocket_socket.py helpers)
# ---------------------------------------------------------------------------

_METADATA_DEFAULTS = dict(description="d", version="1.0", source_hash="x", mandatory=False, id=1)


def _make_step(title="Step", state=TestStateEnum.passed, errors=None, idx=0) -> TestStepExecution:
    return TestStepExecution(
        state=state, title=title, execution_index=idx, id=idx + 100,
        test_case_execution_id=1, errors=errors,
    )


def _make_case(public_id="TC_X_1_1", title="Case", state=TestStateEnum.passed,
               errors=None, steps=None, idx=0) -> TestCaseExecution:
    return TestCaseExecution(
        state=state, public_id=public_id, execution_index=idx, id=idx + 200,
        test_suite_execution_id=1, test_case_metadata_id=1, errors=errors,
        test_case_metadata=TestCaseMetadata(public_id=public_id, title=title, **_METADATA_DEFAULTS),
        test_step_executions=steps or [],
    )


def _make_suite(cases=None, title="Suite", idx=0) -> TestSuiteExecution:
    return TestSuiteExecution(
        state=TestStateEnum.passed, public_id="S1", collection_id="c1",
        execution_index=idx, id=idx + 300, test_run_execution_id=1,
        test_suite_metadata_id=1, test_case_executions=cases or [],
        test_suite_metadata=TestSuiteMetadata(public_id="S1", title=title, **_METADATA_DEFAULTS),
    )


def _make_run(suites=None) -> TestRunExecutionWithChildren:
    return TestRunExecutionWithChildren(
        title="Run", id=1, state=TestStateEnum.executing,
        test_suite_executions=suites or [],
    )


def _make_socket(suites=None, project_config=None) -> TestRunSocket:
    return TestRunSocket(run=_make_run(suites=suites), project_config_dict=project_config)


# ---------------------------------------------------------------------------
# __log_test_run_update
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogTestRunUpdate:
    @pytest.mark.asyncio
    async def test_echoes_state_text(self):
        s = _make_socket()
        update = TestRunUpdate(state=SharedTestStateEnum.PASSED, test_run_execution_id=1)
        with patch("th_cli.test_run.websocket.click.echo") as mock_echo:
            await s._TestRunSocket__log_test_run_update(update)
        mock_echo.assert_called()
        output = " ".join(str(a) for call in mock_echo.call_args_list for a in call[0])
        assert "PASSED" in output.upper() or "passed" in output.lower()

    @pytest.mark.asyncio
    async def test_displays_chip_server_info_on_executing(self):
        s = _make_socket(project_config={
            "dut_config": {"discriminator": 1234, "setup_code": 20202021}
        })
        update = TestRunUpdate(state=SharedTestStateEnum.EXECUTING, test_run_execution_id=1)

        with patch.object(s, "_TestRunSocket__display_manual_pairing_code", new_callable=AsyncMock) as mock_display:
            with patch("th_cli.test_run.websocket.click.echo"):
                await s._TestRunSocket__log_test_run_update(update)

        mock_display.assert_called_once()
        assert s._chip_server_info_displayed is True

    @pytest.mark.asyncio
    async def test_does_not_display_chip_info_twice(self):
        s = _make_socket()
        s._chip_server_info_displayed = True
        update = TestRunUpdate(state=SharedTestStateEnum.EXECUTING, test_run_execution_id=1)

        with patch.object(s, "_TestRunSocket__display_manual_pairing_code", new_callable=AsyncMock) as mock_display:
            with patch("th_cli.test_run.websocket.click.echo"):
                await s._TestRunSocket__log_test_run_update(update)

        mock_display.assert_not_called()


# ---------------------------------------------------------------------------
# __display_manual_pairing_code
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDisplayManualPairingCode:
    @pytest.mark.asyncio
    async def test_skips_when_no_dut_config(self):
        s = _make_socket(project_config={})
        # Should return early without calling get_client
        with patch("th_cli.test_run.websocket.get_client") as mock_get_client:
            await s._TestRunSocket__display_manual_pairing_code()
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_discriminator_missing(self):
        s = _make_socket(project_config={"dut_config": {"setup_code": 12345}})
        with patch("th_cli.test_run.websocket.get_client") as mock_get_client:
            await s._TestRunSocket__display_manual_pairing_code()
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_setup_code_missing(self):
        s = _make_socket(project_config={"dut_config": {"discriminator": 1234}})
        with patch("th_cli.test_run.websocket.get_client") as mock_get_client:
            await s._TestRunSocket__display_manual_pairing_code()
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_api_exception_gracefully(self):
        s = _make_socket(project_config={
            "dut_config": {"discriminator": 1234, "setup_code": 20202021}
        })
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()

        with patch("th_cli.test_run.websocket.get_client", return_value=mock_client):
            with patch("th_cli.test_run.websocket.AsyncApis", side_effect=RuntimeError("boom")):
                with patch("th_cli.test_run.websocket.logger"):
                    await s._TestRunSocket__display_manual_pairing_code()
        # Must not raise

    @pytest.mark.asyncio
    async def test_calls_chip_server_info_api(self):
        s = _make_socket(project_config={
            "dut_config": {"discriminator": 1234, "setup_code": 20202021}
        })
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        mock_chip_info = MagicMock()
        mock_chip_info.node_id_hex = "0x0001"
        mock_chip_info.manual_pairing_code = "34970112332"

        mock_api = AsyncMock()
        mock_api.get_chip_server_info_api_v1_test_run_executions_chip_server_info_get = AsyncMock(
            return_value=mock_chip_info
        )
        mock_async_apis = MagicMock()
        mock_async_apis.test_run_executions_api = mock_api

        with patch("th_cli.test_run.websocket.get_client", return_value=mock_client):
            with patch("th_cli.test_run.websocket.AsyncApis", return_value=mock_async_apis):
                with patch("th_cli.test_run.websocket.click.echo"):
                    await s._TestRunSocket__display_manual_pairing_code()

        mock_api.get_chip_server_info_api_v1_test_run_executions_chip_server_info_get.assert_called_once()
        mock_client.aclose.assert_called_once()


# ---------------------------------------------------------------------------
# __log_test_case_update — browser peer warning and step-error cleanup
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogTestCaseUpdateAdditional:
    def _call(self, socket, update):
        socket._TestRunSocket__log_test_case_update(update)

    def test_browser_peer_warning_when_errors_contain_indicator(self):
        case = _make_case(state=TestStateEnum.failed)
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])
        update = TestCaseUpdate(
            state="failed",
            test_case_execution_index=0,
            test_suite_execution_index=0,
            errors=["peer not found"],
        )
        with patch("th_cli.test_run.websocket.click.echo") as mock_echo:
            with patch("th_cli.test_run.websocket.logger"):
                self._call(s, update)
        output = " ".join(str(a) for call in mock_echo.call_args_list for a in call[0])
        assert "BROWSER" in output.upper()

    def test_browser_peer_warning_from_step_errors(self):
        case = _make_case(state=TestStateEnum.failed)
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])
        # Pre-populate step errors with a browser peer indicator
        s.test_case_step_errors[(0, 0)] = ["create_browser_peer failed"]

        update = TestCaseUpdate(
            state="failed",
            test_case_execution_index=0,
            test_suite_execution_index=0,
        )
        with patch("th_cli.test_run.websocket.click.echo") as mock_echo:
            with patch("th_cli.test_run.websocket.logger"):
                self._call(s, update)
        output = " ".join(str(a) for call in mock_echo.call_args_list for a in call[0])
        assert "BROWSER" in output.upper()

    def test_cleans_up_step_errors_after_case_update(self):
        case = _make_case(state=TestStateEnum.failed)
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])
        s.test_case_step_errors[(0, 0)] = ["some error"]

        update = TestCaseUpdate(
            state="failed",
            test_case_execution_index=0,
            test_suite_execution_index=0,
        )
        with patch("th_cli.test_run.websocket.click.echo"):
            with patch("th_cli.test_run.websocket.logger"):
                self._call(s, update)

        assert (0, 0) not in s.test_case_step_errors

    def test_no_browser_warning_for_passed_case(self):
        case = _make_case(state=TestStateEnum.passed)
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        update = TestCaseUpdate(
            state="passed",
            test_case_execution_index=0,
            test_suite_execution_index=0,
        )
        with patch("th_cli.test_run.websocket.click.echo") as mock_echo:
            with patch("th_cli.test_run.websocket.logger"):
                self._call(s, update)

        output = " ".join(str(a) for call in mock_echo.call_args_list for a in call[0])
        assert "BROWSER" not in output.upper()


# ---------------------------------------------------------------------------
# __handle_log_record
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleLogRecord:
    def test_logs_each_record(self):
        s = _make_socket()
        records = [
            TestLogRecord(level="INFO", timestamp=0.0, message="msg1"),
            TestLogRecord(level="WARNING", timestamp=1.0, message="msg2"),
        ]
        with patch("th_cli.test_run.websocket.logger") as mock_logger:
            s._TestRunSocket__handle_log_record(records)
        assert mock_logger.log.call_count == 2

    def test_uses_record_level_and_message(self):
        s = _make_socket()
        records = [TestLogRecord(level="ERROR", timestamp=0.0, message="boom")]
        with patch("th_cli.test_run.websocket.logger") as mock_logger:
            s._TestRunSocket__handle_log_record(records)
        mock_logger.log.assert_called_once_with("ERROR", "boom")

    def test_empty_records_list(self):
        s = _make_socket()
        with patch("th_cli.test_run.websocket.logger") as mock_logger:
            s._TestRunSocket__handle_log_record([])
        mock_logger.log.assert_not_called()


# ---------------------------------------------------------------------------
# __handle_incoming_socket_message routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleIncomingSocketMessage:
    @pytest.mark.asyncio
    async def test_routes_test_update(self):
        s = _make_socket()
        body = TestRunUpdate(state=SharedTestStateEnum.PASSED, test_run_execution_id=1)
        update = TestUpdate(test_type="test_run", body=body)

        from th_cli.test_run.socket_schemas import SocketMessage
        from th_cli.shared_constants import MessageTypeEnum
        msg = MagicMock()
        msg.payload = update
        msg.type = MessageTypeEnum.TEST_UPDATE

        mock_socket = AsyncMock()

        with patch.object(
            s, "_TestRunSocket__handle_test_update", new_callable=AsyncMock
        ) as mock_handle:
            await s._TestRunSocket__handle_incoming_socket_message(socket=mock_socket, message=msg)

        mock_handle.assert_called_once_with(socket=mock_socket, update=update)

    @pytest.mark.asyncio
    async def test_routes_timeout_notification_silently(self):
        s = _make_socket()
        msg = MagicMock()
        msg.payload = TimeOutNotification(message_id=1)
        msg.type = MessageTypeEnum.TIME_OUT_NOTIFICATION

        mock_socket = AsyncMock()
        # Should not raise and not echo anything
        with patch("th_cli.test_run.websocket.click.echo") as mock_echo:
            await s._TestRunSocket__handle_incoming_socket_message(socket=mock_socket, message=msg)
        # Only the unknown-type echo could fire; for TimeOutNotification it should NOT
        for call in mock_echo.call_args_list:
            assert "Unknown socket message" not in str(call)

    @pytest.mark.asyncio
    async def test_routes_log_records(self):
        s = _make_socket()
        records = [TestLogRecord(level="INFO", timestamp=0.0, message="hi")]
        msg = MagicMock()
        msg.payload = records
        msg.type = MessageTypeEnum.TEST_LOG_RECORDS

        mock_socket = AsyncMock()
        with patch.object(s, "_TestRunSocket__handle_log_record") as mock_log:
            await s._TestRunSocket__handle_incoming_socket_message(socket=mock_socket, message=msg)

        mock_log.assert_called_once_with(records)

    @pytest.mark.asyncio
    async def test_echoes_error_for_unknown_message(self):
        s = _make_socket()
        msg = MagicMock()
        msg.payload = MagicMock()  # not TestUpdate, PromptRequest, list, or TimeOut
        msg.type = "totally_unknown"

        mock_socket = AsyncMock()
        with patch("th_cli.test_run.websocket.click.echo") as mock_echo:
            await s._TestRunSocket__handle_incoming_socket_message(socket=mock_socket, message=msg)

        output = " ".join(str(a) for call in mock_echo.call_args_list for a in call[0])
        assert "Unknown socket message" in output


# ---------------------------------------------------------------------------
# __handle_test_update — all branches
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleTestUpdate:
    @pytest.mark.asyncio
    async def test_routes_step_update(self):
        step = _make_step()
        case = _make_case(steps=[step])
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        body = TestStepUpdate(
            state="passed",
            test_suite_execution_index=0,
            test_case_execution_index=0,
            test_step_execution_index=0,
        )
        update = TestUpdate(test_type="test_step", body=body)

        with patch.object(s, "_TestRunSocket__log_test_step_update") as mock_fn:
            await s._TestRunSocket__handle_test_update(socket=AsyncMock(), update=update)
        mock_fn.assert_called_once_with(body)

    @pytest.mark.asyncio
    async def test_routes_case_update(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        body = TestCaseUpdate(
            state="passed",
            test_suite_execution_index=0,
            test_case_execution_index=0,
        )
        update = TestUpdate(test_type="test_case", body=body)

        with patch.object(s, "_TestRunSocket__log_test_case_update") as mock_fn:
            await s._TestRunSocket__handle_test_update(socket=AsyncMock(), update=update)
        mock_fn.assert_called_once_with(body)

    @pytest.mark.asyncio
    async def test_routes_suite_update(self):
        suite = _make_suite()
        s = _make_socket(suites=[suite])

        body = TestSuiteUpdate(state="passed", test_suite_execution_index=0)
        update = TestUpdate(test_type="test_suite", body=body)

        with patch.object(s, "_TestRunSocket__log_test_suite_update") as mock_fn:
            await s._TestRunSocket__handle_test_update(socket=AsyncMock(), update=update)
        mock_fn.assert_called_once_with(body)

    @pytest.mark.asyncio
    async def test_routes_run_update_and_closes_socket_when_not_executing(self):
        s = _make_socket()
        mock_socket = AsyncMock()

        body = TestRunUpdate(state=SharedTestStateEnum.PASSED, test_run_execution_id=1)
        update = TestUpdate(test_type="test_run", body=body)

        with patch.object(
            s, "_TestRunSocket__log_test_run_update", new_callable=AsyncMock
        ):
            await s._TestRunSocket__handle_test_update(socket=mock_socket, update=update)

        mock_socket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_close_socket_when_still_executing(self):
        s = _make_socket()
        mock_socket = AsyncMock()

        body = TestRunUpdate(state=SharedTestStateEnum.EXECUTING, test_run_execution_id=1)
        update = TestUpdate(test_type="test_run", body=body)

        with patch.object(
            s, "_TestRunSocket__log_test_run_update", new_callable=AsyncMock
        ):
            await s._TestRunSocket__handle_test_update(socket=mock_socket, update=update)

        mock_socket.close.assert_not_called()
