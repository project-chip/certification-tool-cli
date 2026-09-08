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
"""Unit tests for TestRunSocket.connect_websocket() and expected_test_case_count().

Covers the fix for the false-success bug where a websocket connection that
closed (cleanly or abruptly) before the run reached a terminal state was
silently treated as a successfully completed run.
"""

from unittest.mock import AsyncMock, patch

import pytest
import websockets.exceptions as ws_exceptions

from th_cli.api_lib_autogen.models import (
    TestCaseExecution,
    TestCaseMetadata,
    TestRunExecutionWithChildren,
    TestStateEnum,
    TestSuiteExecution,
    TestSuiteMetadata,
)
from th_cli.test_run.websocket import IncompleteTestRunError, TestRunSocket

_METADATA_DEFAULTS = dict(description="d", version="1.0", source_hash="x", mandatory=False, id=1)


def _make_case(public_id="TC_X_1_1", title="Case", idx=0) -> TestCaseExecution:
    return TestCaseExecution(
        state=TestStateEnum.passed,
        public_id=public_id,
        execution_index=idx,
        id=idx + 200,
        test_suite_execution_id=1,
        test_case_metadata_id=1,
        test_case_metadata=TestCaseMetadata(public_id=public_id, title=title, **_METADATA_DEFAULTS),
        test_step_executions=[],
    )


def _make_suite(cases=None, idx=0) -> TestSuiteExecution:
    return TestSuiteExecution(
        state=TestStateEnum.passed,
        public_id="S1",
        collection_id="c1",
        execution_index=idx,
        id=idx + 300,
        test_run_execution_id=1,
        test_suite_metadata_id=1,
        test_case_executions=cases or [],
        test_suite_metadata=TestSuiteMetadata(public_id="S1", title="Suite", **_METADATA_DEFAULTS),
    )


def _make_run(suites=None) -> TestRunExecutionWithChildren:
    return TestRunExecutionWithChildren(
        title="Run", id=1, state=TestStateEnum.executing, test_suite_executions=suites or []
    )


def _make_socket(suites=None) -> TestRunSocket:
    return TestRunSocket(run=_make_run(suites=suites))


class _FakeWSSocket:
    """Fake websocket connection: an async context manager wrapping a mocked recv()/close()."""

    def __init__(self, recv_side_effect):
        self.recv = AsyncMock(side_effect=recv_side_effect)
        self.close = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _patch_connect(fake_socket):
    return patch("th_cli.test_run.websocket.websocket_connect", return_value=fake_socket)


# ---------------------------------------------------------------------------
# expected_test_case_count
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExpectedTestCaseCount:
    def test_no_suites(self):
        s = _make_socket()
        assert s.expected_test_case_count() == 0

    def test_sums_cases_across_suites(self):
        suite1 = _make_suite(cases=[_make_case(idx=0), _make_case(idx=1)])
        suite2 = _make_suite(cases=[_make_case(idx=0)], idx=1)
        s = _make_socket(suites=[suite1, suite2])
        assert s.expected_test_case_count() == 3


# ---------------------------------------------------------------------------
# connect_websocket — premature/abrupt closure detection
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConnectWebsocketIncompleteClosure:
    @pytest.mark.asyncio
    async def test_clean_close_before_run_finished_raises(self):
        """Socket closes cleanly, but no terminal TestRunUpdate was ever received."""
        s = _make_socket()
        fake_socket = _FakeWSSocket(recv_side_effect=ws_exceptions.ConnectionClosedOK(None, None))

        with _patch_connect(fake_socket):
            with pytest.raises(IncompleteTestRunError):
                await s.connect_websocket()

        # Run never finished, so the explicit close()-on-finish path must not fire.
        fake_socket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_clean_close_after_run_finished_does_not_raise(self):
        """Existing behavior: clean close during the post-terminal drain period is fine."""
        s = _make_socket()
        s._run_finished = True
        fake_socket = _FakeWSSocket(recv_side_effect=ws_exceptions.ConnectionClosedOK(None, None))

        with _patch_connect(fake_socket):
            await s.connect_websocket()  # must not raise

        fake_socket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_abrupt_close_before_run_finished_raises(self):
        """Socket drops (no close handshake) before the run reached a terminal state."""
        s = _make_socket()
        fake_socket = _FakeWSSocket(recv_side_effect=ws_exceptions.ConnectionClosedError(None, None))

        with _patch_connect(fake_socket):
            with pytest.raises(IncompleteTestRunError):
                await s.connect_websocket()

        fake_socket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_abrupt_close_after_run_finished_does_not_raise(self):
        """Existing behavior: a dropped close handshake after the run finished is tolerated."""
        s = _make_socket()
        s._run_finished = True
        fake_socket = _FakeWSSocket(recv_side_effect=ws_exceptions.ConnectionClosedError(None, None))

        with _patch_connect(fake_socket):
            await s.connect_websocket()  # must not raise

        fake_socket.close.assert_called_once()
