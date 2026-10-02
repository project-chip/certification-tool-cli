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
import asyncio

import click
from pydantic import ValidationError

from th_cli.api_lib_autogen.api_client import AsyncApis
from th_cli.api_lib_autogen.exceptions import ApiException
from th_cli.colorize import colorize_warning
from th_cli.shared_constants import TestStateEnum
from th_cli.test_run import logging as test_logging
from th_cli.test_run.socket_schemas import TestLogRecord

# How often to poll the backend for the run's persisted state while waiting for
# its final DB commit.
PERSIST_POLL_INTERVAL_S = 0.25

# Safety net only, in case the backend dies before committing. The final commit
# normally lands well under a second after the terminal state update, but a run
# with a very large log is written in one commit and can take longer.
PERSIST_TIMEOUT_S = 120.0

# Mirrors the backend's TestRun.completed() contract (state not in
# [PENDING, EXECUTING]), compared by value since the API model's enum differs
# from the shared one.
_NON_TERMINAL_STATE_VALUES = frozenset({TestStateEnum.PENDING.value, TestStateEnum.EXECUTING.value})


async def sync_log_file_from_backend(async_apis: AsyncApis, run_id: int, log_path: str) -> bool:
    """Replace the run's local log file with the log persisted by the backend.

    The local file is built from websocket log records, which can miss the
    trailing batch the backend flushes around the time the run completes. The
    backend commits the run's terminal state and its complete log in a single
    DB commit at the end of the run, so once the terminal state is readable via
    the API, the persisted log is complete - no grace-period guessing needed.

    Failures are reported as warnings and leave the websocket-built file in
    place, so a problem fetching the log never fails the run itself.

    Returns:
        True if the log file was replaced with the backend's log.
    """
    test_run_executions_api = async_apis.test_run_executions_api
    loop = asyncio.get_running_loop()
    deadline = loop.time() + PERSIST_TIMEOUT_S

    try:
        while True:
            execution = await test_run_executions_api.read_test_run_execution_api_v1_test_run_executions__id__get(
                id=run_id
            )
            state = getattr(execution.state, "value", execution.state)
            if state not in _NON_TERMINAL_STATE_VALUES:
                break
            if loop.time() >= deadline:
                click.echo(
                    colorize_warning(
                        f"Timed out after {PERSIST_TIMEOUT_S:.0f}s waiting for the backend to save the run's log; "
                        "the local log file may be missing its final lines."
                    ),
                    err=True,
                )
                return False
            await asyncio.sleep(PERSIST_POLL_INTERVAL_S)

        # The generated client is typed as returning None, but returns the body text.
        download_log = test_run_executions_api.download_log_api_v1_test_run_executions__id__log_get
        log_content: object = await download_log(  # type: ignore[func-returns-value]
            id=run_id, json_entries=True, download=False
        )
    except ApiException as e:
        click.echo(
            colorize_warning(
                f"Could not fetch the run's log from the backend ({e}); "
                "the local log file may be missing its final lines."
            ),
            err=True,
        )
        return False

    # With json_entries=True the backend returns one JSON-encoded entry per
    # line. Parse them all before touching the local file, so a malformed
    # response leaves the websocket-built file intact.
    try:
        entries = [
            TestLogRecord.model_validate_json(line)
            for line in (log_content.splitlines() if isinstance(log_content, str) else [])
            if line.strip()
        ]
    except ValidationError as e:
        click.echo(colorize_warning(f"Could not parse the run's log from the backend: {e}"), err=True)
        return False

    # An empty log isn't expected for a run that reached a terminal state (the
    # backend logs at least the run's start and end) - keep what we have rather
    # than replacing it with nothing.
    if not entries:
        return False

    try:
        test_logging.write_log_file_from_entries(log_path, entries)
    except (OSError, ValueError) as e:
        click.echo(colorize_warning(f"Could not write the run's log to {log_path}: {e}"), err=True)
        return False
    return True
