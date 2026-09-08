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
"""Unit tests for TestRunSocket in websocket.py."""

from unittest.mock import AsyncMock, patch

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
from th_cli.test_run.socket_schemas import (
    TestCaseUpdate,
    TestLogRecord,
    TestRunUpdate,
    TestStepUpdate,
    TestSuiteUpdate,
    TestUpdate,
)
from th_cli.test_run.websocket import TestRunSocket

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_METADATA_DEFAULTS = dict(
    description="desc",
    version="1.0",
    source_hash="abc",
    mandatory=False,
    id=1,
)


def _make_step(title="Step 1", state=TestStateEnum.passed, errors=None, idx=0) -> TestStepExecution:
    return TestStepExecution(
        state=state,
        title=title,
        execution_index=idx,
        id=idx + 100,
        test_case_execution_id=1,
        errors=errors,
    )


def _make_case(
    public_id="TC_FOO_1_1",
    title="Case 1",
    state=TestStateEnum.passed,
    errors=None,
    steps=None,
    idx=0,
) -> TestCaseExecution:
    return TestCaseExecution(
        state=state,
        public_id=public_id,
        execution_index=idx,
        id=idx + 200,
        test_suite_execution_id=1,
        test_case_metadata_id=1,
        errors=errors,
        test_case_metadata=TestCaseMetadata(
            public_id=public_id,
            title=title,
            **_METADATA_DEFAULTS,
        ),
        test_step_executions=steps or [],
    )


def _make_suite(cases=None, title="Suite 1", idx=0) -> TestSuiteExecution:
    return TestSuiteExecution(
        state=TestStateEnum.passed,
        public_id="SUITE_1",
        collection_id="collection_1",
        execution_index=idx,
        id=idx + 300,
        test_run_execution_id=1,
        test_suite_metadata_id=1,
        test_case_executions=cases or [],
        test_suite_metadata=TestSuiteMetadata(
            public_id="SUITE_1",
            title=title,
            **_METADATA_DEFAULTS,
        ),
    )


def _make_run(suites=None) -> TestRunExecutionWithChildren:
    return TestRunExecutionWithChildren(
        title="Test Run",
        id=1,
        state=TestStateEnum.executing,
        test_suite_executions=suites or [],
    )


def _make_socket(suites=None, project_config=None) -> TestRunSocket:
    run = _make_run(suites=suites)
    return TestRunSocket(run=run, project_config_dict=project_config)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTestRunSocketInit:
    def test_run_stored(self):
        run = _make_run()
        s = TestRunSocket(run=run)
        assert s.run is run

    def test_project_config_defaults_to_empty_dict(self):
        s = TestRunSocket(run=_make_run())
        assert s.project_config_dict == {}

    def test_project_config_stored_when_provided(self):
        cfg = {"key": "value"}
        s = TestRunSocket(run=_make_run(), project_config_dict=cfg)
        assert s.project_config_dict is cfg

    def test_test_case_step_errors_initially_empty(self):
        s = TestRunSocket(run=_make_run())
        assert s.test_case_step_errors == {}

    def test_chip_server_info_not_displayed_initially(self):
        s = TestRunSocket(run=_make_run())
        assert s._chip_server_info_displayed is False


# ---------------------------------------------------------------------------
# __log_test_step_update — error accumulation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogTestStepUpdate:

    def _call(self, socket: TestRunSocket, update: TestStepUpdate):
        socket._TestRunSocket__log_test_step_update(update)

    def _update(self, errors=None, step_idx=0, case_idx=0, suite_idx=0) -> TestStepUpdate:
        return TestStepUpdate(
            state="passed",
            test_step_execution_index=step_idx,
            test_case_execution_index=case_idx,
            test_suite_execution_index=suite_idx,
            errors=errors,
        )

    def test_errors_accumulated_into_dict(self):
        step = _make_step(errors=["some error"])
        case = _make_case(steps=[step])
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        self._call(s, self._update(errors=["some error"]))

        assert s.test_case_step_errors[(0, 0)] == ["some error"]

    def test_multiple_steps_extend_same_case_list(self):
        step0 = _make_step(errors=["err0"], idx=0)
        step1 = _make_step(errors=["err1"], idx=1)
        case = _make_case(steps=[step0, step1])
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        self._call(s, self._update(errors=["err0"], step_idx=0))
        self._call(s, self._update(errors=["err1"], step_idx=1))

        assert s.test_case_step_errors[(0, 0)] == ["err0", "err1"]

    def test_no_entry_when_update_has_no_errors(self):
        step = _make_step()
        case = _make_case(steps=[step])
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        self._call(s, self._update(errors=None))

        assert (0, 0) not in s.test_case_step_errors

    def test_errors_keyed_by_suite_and_case_index(self):
        step = _make_step(errors=["e"], idx=0)
        case0 = _make_case(steps=[step], idx=0)
        case1 = _make_case(steps=[step], idx=1)
        suite = _make_suite(cases=[case0, case1])
        s = _make_socket(suites=[suite])

        self._call(s, self._update(errors=["err_case0"], case_idx=0))
        self._call(s, self._update(errors=["err_case1"], case_idx=1))

        assert s.test_case_step_errors[(0, 0)] == ["err_case0"]
        assert s.test_case_step_errors[(0, 1)] == ["err_case1"]


# ---------------------------------------------------------------------------
# __log_test_case_update — error cleanup
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogTestCaseUpdate:

    def _call(self, socket: TestRunSocket, update: TestCaseUpdate):
        socket._TestRunSocket__log_test_case_update(update)

    def _update(self, case_idx=0, suite_idx=0, errors=None, state="failed") -> TestCaseUpdate:
        return TestCaseUpdate(
            state=state,
            test_case_execution_index=case_idx,
            test_suite_execution_index=suite_idx,
            errors=errors,
        )

    def test_step_errors_cleaned_up_after_case_update(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])
        s.test_case_step_errors[(0, 0)] = ["some error"]

        self._call(s, self._update(errors=None))

        assert (0, 0) not in s.test_case_step_errors

    def test_failed_case_echoes_state(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        with patch("click.echo") as mock_echo:
            self._call(s, self._update(state="failed"))

        echoed = " ".join(str(c) for call in mock_echo.call_args_list for c in call[0])
        assert "failed" in echoed.lower()

    def test_passed_case_echoes_state(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        with patch("click.echo") as mock_echo:
            self._call(s, self._update(state="passed"))

        echoed = " ".join(str(c) for call in mock_echo.call_args_list for c in call[0])
        assert "passed" in echoed.lower()

    def test_browser_peer_warning_shown_for_peer_not_found(self):
        case = _make_case(public_id="TC_WEBRTC_1_6")
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        with patch("click.echo") as mock_echo:
            self._call(s, self._update(errors=["Peer not found"]))

        echoed = " ".join(str(c) for call in mock_echo.call_args_list for c in call[0])
        assert "BROWSER TAB REQUIRED" in echoed

    def test_browser_peer_warning_not_shown_for_unrelated_failure(self):
        case = _make_case(public_id="TC_CLUSTER_1_1")
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        with patch("click.echo") as mock_echo:
            self._call(s, self._update(errors=["attribute read failed"]))

        echoed = " ".join(str(c) for call in mock_echo.call_args_list for c in call[0])
        assert "BROWSER TAB REQUIRED" not in echoed

    def test_terminal_state_recorded_in_final_states(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])
        self._call(s, self._update(state="passed"))
        assert s.test_case_final_states[(0, 0)] == "passed"

    def test_later_update_overwrites_earlier_final_state_for_same_case(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])
        self._call(s, self._update(state="error"))
        self._call(s, self._update(state="passed"))
        assert s.test_case_final_states[(0, 0)] == "passed"

    def test_non_terminal_state_not_recorded(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])
        self._call(s, self._update(state="executing"))
        assert (0, 0) not in s.test_case_final_states


# ---------------------------------------------------------------------------
# Results summary / exit code tallying (issue #1095)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResultsSummary:

    def _call(self, socket: TestRunSocket, update: TestCaseUpdate):
        socket._TestRunSocket__log_test_case_update(update)

    def _update(self, case_idx=0, suite_idx=0, state="passed") -> TestCaseUpdate:
        return TestCaseUpdate(
            state=state,
            test_case_execution_index=case_idx,
            test_suite_execution_index=suite_idx,
            errors=None,
        )

    def _socket_with_cases(self, states: list[str]) -> TestRunSocket:
        cases = [_make_case(idx=i) for i in range(len(states))]
        suite = _make_suite(cases=cases)
        s = _make_socket(suites=[suite])
        for i, state in enumerate(states):
            self._call(s, self._update(case_idx=i, state=state))
        return s

    def test_no_cases_executed_summary(self):
        s = _make_socket()
        assert s.format_results_summary() == "0 test cases executed"
        assert s.has_test_failures() is False
        assert s.test_case_result_counts() == {}

    def test_all_passed_no_failures(self):
        s = self._socket_with_cases(["passed", "passed", "passed"])
        assert s.has_test_failures() is False
        assert s.format_results_summary() == "3 passed"

    def test_mixed_states_counted_and_ordered(self):
        s = self._socket_with_cases(["passed", "failed", "error", "not_applicable", "cancelled"])
        assert s.has_test_failures() is True
        assert s.format_results_summary() == "1 passed, 1 failed, 1 error, 1 not applicable, 1 cancelled"

    def test_not_applicable_and_cancelled_do_not_count_as_failures(self):
        s = self._socket_with_cases(["passed", "not_applicable", "cancelled"])
        assert s.has_test_failures() is False

    def test_error_state_counts_as_failure(self):
        s = self._socket_with_cases(["passed", "error"])
        assert s.has_test_failures() is True

    def test_case_updated_more_than_once_counted_once(self):
        s = self._socket_with_cases(["executing"])
        self._call(s, self._update(case_idx=0, state="passed"))
        assert s.test_case_result_counts() == {"passed": 1}


# ---------------------------------------------------------------------------
# __handle_test_update — dispatch
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHandleTestUpdate:

    @pytest.mark.asyncio
    async def test_step_update_routed_correctly(self):
        step = _make_step()
        case = _make_case(steps=[step])
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        update = TestUpdate(
            test_type="test_step",
            body=TestStepUpdate(
                state="passed", test_step_execution_index=0, test_case_execution_index=0, test_suite_execution_index=0
            ),
        )
        with patch.object(s, "_TestRunSocket__log_test_step_update") as mock_fn:
            await s._TestRunSocket__handle_test_update(update=update)

        mock_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_case_update_routed_correctly(self):
        case = _make_case()
        suite = _make_suite(cases=[case])
        s = _make_socket(suites=[suite])

        update = TestUpdate(
            test_type="test_case",
            body=TestCaseUpdate(state="passed", test_case_execution_index=0, test_suite_execution_index=0),
        )
        with patch.object(s, "_TestRunSocket__log_test_case_update") as mock_fn:
            await s._TestRunSocket__handle_test_update(update=update)

        mock_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_suite_update_routed_correctly(self):
        suite = _make_suite()
        s = _make_socket(suites=[suite])

        update = TestUpdate(
            test_type="test_suite",
            body=TestSuiteUpdate(state="passed", test_suite_execution_index=0),
        )
        with patch.object(s, "_TestRunSocket__log_test_suite_update") as mock_fn:
            await s._TestRunSocket__handle_test_update(update=update)

        mock_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_update_executing_leaves_run_not_finished(self):
        s = _make_socket()

        update = TestUpdate(test_type="test_run", body=TestRunUpdate(state="executing", test_run_execution_id=1))
        with patch.object(s, "_TestRunSocket__log_test_run_update", new_callable=AsyncMock):
            await s._TestRunSocket__handle_test_update(update=update)

        assert s._run_finished is False

    @pytest.mark.asyncio
    async def test_run_update_non_executing_marks_run_finished(self):
        s = _make_socket()

        update = TestUpdate(test_type="test_run", body=TestRunUpdate(state="passed", test_run_execution_id=1))
        with patch.object(s, "_TestRunSocket__log_test_run_update", new_callable=AsyncMock):
            await s._TestRunSocket__handle_test_update(update=update)

        assert s._run_finished is True

    @pytest.mark.asyncio
    async def test_run_update_pending_leaves_run_not_finished(self):
        # Regression test: "pending" is non-terminal (backend's TestRun.completed()
        # excludes both PENDING and EXECUTING), so it must not close the socket.
        # A prior implementation used a negation check (`state != "executing"`)
        # that misclassified any non-"executing" state, including "pending", as
        # terminal.
        s = _make_socket()

        update = TestUpdate(test_type="test_run", body=TestRunUpdate(state="pending", test_run_execution_id=1))
        with patch.object(s, "_TestRunSocket__log_test_run_update", new_callable=AsyncMock):
            await s._TestRunSocket__handle_test_update(update=update)

        assert s._run_finished is False

    @pytest.mark.asyncio
    async def test_handle_log_record_logs_every_record(self):
        s = _make_socket()
        records = [
            TestLogRecord(level="INFO", timestamp=0.0, message=f"msg{i}") for i in range(3)
        ]

        with patch("th_cli.test_run.websocket.logger") as mock_logger:
            await s._TestRunSocket__handle_log_record(records)

        assert mock_logger.log.call_count == 3
        for record in records:
            mock_logger.log.assert_any_call(record.level, record.message)
