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

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

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


# ---------------------------------------------------------------------------
# connect_websocket — closing after the terminal TestRunUpdate
# ---------------------------------------------------------------------------


def _terminal_run_update(**body) -> str:
    return json.dumps(
        {
            "type": "test_update",
            "payload": {
                "test_type": "test_run",
                "body": {"state": "passed", "test_run_execution_id": 1, **body},
            },
        }
    )


_TRAILING_LOG_RECORDS = json.dumps(
    {"type": "test_log_records", "payload": [{"level": "INFO", "timestamp": 1.0, "message": "trailing"}]}
)


@pytest.mark.unit
class TestConnectWebsocketAfterTerminalUpdate:
    @pytest.mark.asyncio
    async def test_logs_complete_closes_without_draining(self):
        """The backend sent the terminal update after the run's last log records."""
        s = _make_socket()
        fake_socket = _FakeWSSocket(
            recv_side_effect=[_terminal_run_update(logs_complete=True), AssertionError("must not drain")]
        )

        with _patch_connect(fake_socket), patch("th_cli.test_run.websocket.DRAIN_TIMEOUT_S", 3600):
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

        assert fake_socket.recv.await_count == 1
        fake_socket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_incomplete_warns_and_closes_without_draining(self, capsys):
        s = _make_socket()
        fake_socket = _FakeWSSocket(
            recv_side_effect=[_terminal_run_update(logs_complete=False), AssertionError("must not drain")]
        )

        with _patch_connect(fake_socket), patch("th_cli.test_run.websocket.DRAIN_TIMEOUT_S", 3600):
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

        assert fake_socket.recv.await_count == 1
        assert "couldn't send all of the run's log records" in capsys.readouterr().err

    @pytest.mark.asyncio
    async def test_older_backend_drains_trailing_log_records(self):
        """No logs_complete field: the backend's last log records may still follow."""
        s = _make_socket()
        fake_socket = _FakeWSSocket(
            recv_side_effect=[_terminal_run_update(), _TRAILING_LOG_RECORDS, asyncio.TimeoutError()]
        )

        with _patch_connect(fake_socket), patch("th_cli.test_run.websocket.logger") as mock_logger:
            await s.connect_websocket()

        mock_logger.log.assert_any_call("INFO", "trailing")
        assert fake_socket.recv.await_count == 3
        fake_socket.close.assert_called_once()


# ---------------------------------------------------------------------------
# connect_websocket — prompts are answered without blocking the read loop
# ---------------------------------------------------------------------------

_PROMPT_ID = 7

_OPTIONS_PROMPT = json.dumps(
    {
        "type": "options_request",
        "payload": {"prompt": "Make sure the DUT is in Commissioning Mode", "timeout": 60, "message_id": _PROMPT_ID,
                    "options": {"DONE": 1, "FAILED": 2}},
    }
)
_PROMPT_TIMED_OUT = json.dumps({"type": "time_out_notification", "payload": {"message_id": _PROMPT_ID}})
_LOG_RECORDS = json.dumps(
    {"type": "test_log_records", "payload": [{"level": "INFO", "timestamp": 1.0, "message": "pairing logs"}]}
)


def _yielding_recv(messages, delay=0):
    """recv() stand-in that hands over the messages in order, yielding to the loop before each one."""
    pending = list(messages)

    async def recv():
        await asyncio.sleep(delay)
        return pending.pop(0)

    return recv


class _BlockedPrompt:
    """handle_prompt stand-in that stays open until released, recording how it ended."""

    def __init__(self):
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.cancelled = False

    async def __call__(self, **_kwargs):
        self.started.set()
        try:
            await self.release.wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


@pytest.mark.unit
class TestConnectWebsocketPrompts:
    @pytest.mark.asyncio
    async def test_log_records_are_processed_while_prompt_is_open(self):
        """The prompt only returns after a log record was handled: the read loop must not wait for it."""
        s = _make_socket()
        prompt = _BlockedPrompt()
        fake_socket = _FakeWSSocket(
            recv_side_effect=_yielding_recv([_OPTIONS_PROMPT, _LOG_RECORDS, _terminal_run_update(logs_complete=True)])
        )

        with (
            _patch_connect(fake_socket),
            patch("th_cli.test_run.websocket.handle_prompt", new=prompt),
            patch("th_cli.test_run.websocket.logger") as mock_logger,
        ):
            mock_logger.log.side_effect = lambda *_: prompt.release.set()
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

        mock_logger.log.assert_any_call("INFO", "pairing logs")
        assert prompt.started.is_set()
        assert not prompt.cancelled

    @pytest.mark.asyncio
    async def test_timeout_notification_cancels_open_prompt(self, capsys):
        s = _make_socket()
        prompt = _BlockedPrompt()
        fake_socket = _FakeWSSocket(
            recv_side_effect=_yielding_recv(
                [_OPTIONS_PROMPT, _PROMPT_TIMED_OUT, _terminal_run_update(logs_complete=True)]
            )
        )

        with _patch_connect(fake_socket), patch("th_cli.test_run.websocket.handle_prompt", new=prompt):
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

        assert prompt.cancelled
        assert capsys.readouterr().err.count("Prompt timed out") == 1

    @pytest.mark.asyncio
    async def test_timeout_notification_for_unknown_prompt_is_ignored(self, capsys):
        s = _make_socket()
        fake_socket = _FakeWSSocket(
            recv_side_effect=_yielding_recv([_PROMPT_TIMED_OUT, _terminal_run_update(logs_complete=True)])
        )

        with _patch_connect(fake_socket):
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

        assert "Prompt timed out" not in capsys.readouterr().err

    @pytest.mark.asyncio
    async def test_open_prompt_is_cancelled_when_run_finishes(self):
        s = _make_socket()
        prompt = _BlockedPrompt()
        fake_socket = _FakeWSSocket(
            recv_side_effect=_yielding_recv([_OPTIONS_PROMPT, _terminal_run_update(logs_complete=True)])
        )

        with _patch_connect(fake_socket), patch("th_cli.test_run.websocket.handle_prompt", new=prompt):
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

        assert prompt.started.is_set()
        assert prompt.cancelled

    @pytest.mark.asyncio
    async def test_prompt_failure_is_reported_and_raised(self, capsys):
        s = _make_socket()
        messages = [_OPTIONS_PROMPT] + [_LOG_RECORDS] * 5 + [_terminal_run_update(logs_complete=True)]
        fake_socket = _FakeWSSocket(recv_side_effect=_yielding_recv(messages))

        with (
            _patch_connect(fake_socket),
            patch("th_cli.test_run.websocket.handle_prompt", new=AsyncMock(side_effect=EOFError("stdin closed"))),
            patch("th_cli.test_run.websocket.logger"),
        ):
            with pytest.raises(EOFError):
                await asyncio.wait_for(s.connect_websocket(), timeout=5)

        assert "Prompt handling failed" in capsys.readouterr().err

    @pytest.mark.asyncio
    async def test_prompts_are_answered_one_at_a_time(self):
        s = _make_socket()
        second_prompt = _OPTIONS_PROMPT.replace(f'"message_id": {_PROMPT_ID}', f'"message_id": {_PROMPT_ID + 1}')
        running = 0
        max_running = 0

        async def prompt(**_kwargs):
            nonlocal running, max_running
            running += 1
            max_running = max(max_running, running)
            await asyncio.sleep(0.05)
            running -= 1

        fake_socket = _FakeWSSocket(
            recv_side_effect=_yielding_recv([_OPTIONS_PROMPT, second_prompt, _terminal_run_update(logs_complete=True)])
        )
        # The run finishing cancels what is still open, so keep the loop alive until both prompts are done.
        original = s._TestRunSocket__cancel_pending_prompts

        async def wait_then_cancel():
            await asyncio.gather(*s._prompt_tasks.values(), return_exceptions=True)
            await original()

        with (
            _patch_connect(fake_socket),
            patch("th_cli.test_run.websocket.handle_prompt", new=prompt),
            patch.object(s, "_TestRunSocket__cancel_pending_prompts", wait_then_cancel),
        ):
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

        assert max_running == 1


# ---------------------------------------------------------------------------
# CHIP server info is shown before the prompt, not between the prompt and its answer
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestChipServerInfoBeforePrompt:
    @staticmethod
    async def _run(s, show, prompt, messages, delay=0):
        fake_socket = _FakeWSSocket(recv_side_effect=_yielding_recv(messages, delay=delay))
        with (
            _patch_connect(fake_socket),
            patch.object(s, "_TestRunSocket__display_manual_pairing_code", new=show),
            patch("th_cli.test_run.websocket.handle_prompt", new=prompt),
            patch("th_cli.test_run.websocket.logger"),
        ):
            await asyncio.wait_for(s.connect_websocket(), timeout=5)

    @pytest.mark.asyncio
    async def test_info_is_shown_before_the_prompt(self):
        s = _make_socket()
        s._chip_server_watcher = MagicMock()  # the run is executing
        order = []

        async def show():
            order.append("info")

        async def prompt(**_kwargs):
            order.append("prompt")

        messages = [_OPTIONS_PROMPT] + [_LOG_RECORDS] * 5 + [_terminal_run_update(logs_complete=True)]
        await self._run(s, show, prompt, messages)

        assert order == ["info", "prompt"]

    @pytest.mark.asyncio
    async def test_no_info_before_the_prompt_when_run_is_not_executing(self):
        s = _make_socket()
        show = AsyncMock()
        prompt = AsyncMock()

        messages = [_OPTIONS_PROMPT] + [_LOG_RECORDS] * 5 + [_terminal_run_update(logs_complete=True)]
        await self._run(s, show, prompt, messages)

        show.assert_not_called()
        prompt.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_slow_info_does_not_hold_the_prompt_back(self):
        s = _make_socket()
        s._chip_server_watcher = MagicMock()
        shown = []

        async def show():
            await asyncio.Event().wait()  # never answers

        async def prompt(**_kwargs):
            shown.append("prompt")

        with patch("th_cli.test_run.websocket.CHIP_SERVER_INFO_BEFORE_PROMPT_TIMEOUT_S", 0.01):
            await self._run(s, show, prompt, [_OPTIONS_PROMPT, _terminal_run_update(logs_complete=True)], delay=0.05)

        assert shown == ["prompt"]

    @pytest.mark.asyncio
    async def test_info_is_fetched_one_caller_at_a_time(self):
        """The watcher and a prompt can ask at once; only one may fetch, so the banner shows once."""
        s = _make_socket()
        running = 0
        peak = 0

        async def fetch():
            nonlocal running, peak
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.01)
            running -= 1

        with patch.object(s, "_TestRunSocket__fetch_and_display_chip_server_info", new=fetch):
            await asyncio.gather(
                s._TestRunSocket__display_manual_pairing_code(),
                s._TestRunSocket__display_manual_pairing_code(),
            )

        assert peak == 1
