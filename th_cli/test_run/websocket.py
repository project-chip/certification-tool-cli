#
# Copyright (c) 2025 Project CHIP Authors
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
import websockets
from loguru import logger
from pydantic import ValidationError
from websockets.client import WebSocketClientProtocol
from websockets.client import connect as websocket_connect

from th_cli.api_lib_autogen.models import (
    TestCaseExecution,
    TestRunExecutionWithChildren,
    TestStepExecution,
    TestSuiteExecution,
)
from th_cli.colorize import HierarchyEnum, colorize_error, colorize_hierarchy_prefix, colorize_state
from th_cli.config import config
from th_cli.shared_constants import MessageTypeEnum

from .prompt_manager import handle_file_upload_request, handle_prompt
from .socket_schemas import (
    PromptRequest,
    SocketMessage,
    TestCaseUpdate,
    TestLogRecord,
    TestRunUpdate,
    TestStepUpdate,
    TestSuiteUpdate,
    TestUpdate,
    TimeOutNotification,
)

WEBSOCKET_URL = f"ws://{config.hostname}/api/v1/ws"


class TestRunSocket:
    def __init__(self, run: TestRunExecutionWithChildren):
        self.run = run
        # Track test step errors for WebRTC detection
        # Key: (suite_index, case_index), Value: list of error strings from all steps
        self.test_case_step_errors: dict[tuple[int, int], list[str]] = {}

    async def connect_websocket(self) -> None:

        async with websocket_connect(WEBSOCKET_URL, ping_timeout=None) as socket:
            try:
                while True:
                    try:
                        message = await socket.recv()
                    except websockets.exceptions.ConnectionClosedOK:
                        break

                    # skip messages that are bytes, as we're expecting a string.\
                    if not isinstance(message, str):
                        click.echo(
                            colorize_error("Failed to parse incoming websocket message. got bytes, expected text"),
                            err=True,
                        )
                        continue
                    try:
                        message_obj = SocketMessage.parse_raw(message)
                        await self.__handle_incoming_socket_message(socket=socket, message=message_obj)
                    except ValidationError as e:
                        click.echo(colorize_error(f"Received invalid socket message: {message}"), err=True)
                        click.echo(colorize_error(e.json()), err=True)
            finally:
                pass  # Cleanup if needed

    async def __handle_incoming_socket_message(self, socket: WebSocketClientProtocol, message: SocketMessage) -> None:
        if isinstance(message.payload, TestUpdate):
            await self.__handle_test_update(socket=socket, update=message.payload)
        elif isinstance(message.payload, PromptRequest):
            # Debug: log the message type
            logger.debug(f"Received prompt with type: {message.type}")

            # Check message type to route to appropriate handler
            if message.type == MessageTypeEnum.FILE_UPLOAD_REQUEST:
                await handle_file_upload_request(socket=socket, request=message.payload)
            else:
                # Pass both the request and the message type to handle_prompt
                await handle_prompt(socket=socket, request=message.payload, message_type=message.type)
        elif message.type == MessageTypeEnum.TEST_LOG_RECORDS and isinstance(message.payload, list):
            self.__handle_log_record(message.payload)
        elif isinstance(message.payload, TimeOutNotification):
            # ignore time_out_notification as we handle timeout our selves
            pass
        else:
            click.echo(
                colorize_error(f"Unknown socket message type: {message.type} | payload: {message.payload}."),
                err=True,
            )

    async def __handle_test_update(self, socket: WebSocketClientProtocol, update: TestUpdate) -> None:
        if isinstance(update.body, TestStepUpdate):
            self.__log_test_step_update(update.body)
        elif isinstance(update.body, TestCaseUpdate):
            self.__log_test_case_update(update.body)
        elif isinstance(update.body, TestSuiteUpdate):
            self.__log_test_suite_update(update.body)
        elif isinstance(update.body, TestRunUpdate):
            self.__log_test_run_update(update.body)
            if update.body.state != "executing":
                # Test run ended disconnect.
                await socket.close()

    def __log_test_run_update(self, update: TestRunUpdate) -> None:
        test_run_text = colorize_hierarchy_prefix("Test Run", HierarchyEnum.TEST_RUN.value)
        colored_state = colorize_state(update.state.value)
        click.echo(f"{test_run_text} {colored_state}")

    def __log_test_suite_update(self, update: TestSuiteUpdate) -> None:
        suite = self.__suite(update.test_suite_execution_index)
        title = suite.test_suite_metadata.title
        colored_title = colorize_hierarchy_prefix(title, HierarchyEnum.TEST_SUITE.value)
        colored_state = colorize_state(update.state.value)
        click.echo(f"  - {colored_title} {colored_state}")

    def __log_test_case_update(self, update: TestCaseUpdate) -> None:
        case = self.__case(index=update.test_case_execution_index, suite_index=update.test_suite_execution_index)
        title = case.test_case_metadata.title
        public_id = case.test_case_metadata.public_id
        colored_title = colorize_hierarchy_prefix(title, HierarchyEnum.TEST_CASE.value)
        colored_state = colorize_state(update.state.value)
        click.echo(f"      - {colored_title} {colored_state}")

        # Check if test failed/errored due to WebRTC/browser requirements
        # Collect errors from both the test case update and tracked step errors
        if update.state.value in ("failed", "error"):
            all_errors = []

            # Add test case errors from the update
            if update.errors:
                all_errors.extend(update.errors)
                logger.debug(f"Test case has {len(update.errors)} error(s): {update.errors}")

            # Add any test step errors we tracked for this test case
            case_key = (update.test_suite_execution_index, update.test_case_execution_index)
            if case_key in self.test_case_step_errors:
                all_errors.extend(self.test_case_step_errors[case_key])
                logger.debug(
                    f"Found {len(self.test_case_step_errors[case_key])} tracked step error(s): {self.test_case_step_errors[case_key]}"
                )
            else:
                logger.debug(f"No tracked step errors found for test case {case_key}")

            # Fallback: Check if this is a known WebRTC test by public_id
            is_webrtc_test = public_id in {"TC_WEBRTC_1_6"}

            if all_errors:
                error_text = " ".join(all_errors).lower()
                logger.debug(f"Checking error text for WebRTC indicators: {error_text[:200]}")
                # Check for common WebRTC/browser-related error indicators
                webrtc_indicators = [
                    "browserpeerconnection",
                    "webrtc",
                    "browser peer",
                    "ws://backend/api/v1/ws/webrtc",
                    "create_browser_peer",
                ]
                if any(indicator in error_text for indicator in webrtc_indicators):
                    is_webrtc_test = True

            # Display warning if this is a WebRTC test
            if is_webrtc_test:
                click.echo("")
                click.echo(colorize_error("⚠️  TWO-WAY TALK TEST NOT SUPPORTED IN CLI"), err=True)
                click.echo(colorize_error(f"   {title} requires a browser WebRTC implementation."), err=True)
                click.echo(colorize_error("   This test cannot run from the CLI. Please use the Web UI."), err=True)
                click.echo("")
            elif not all_errors:
                logger.debug(f"Test case {public_id} ({case_key}) failed but has no error messages")

            # Clean up tracked errors for this test case
            if case_key in self.test_case_step_errors:
                del self.test_case_step_errors[case_key]

    def __log_test_step_update(self, update: TestStepUpdate) -> None:
        step = self.__step(
            index=update.test_step_execution_index,
            case_index=update.test_case_execution_index,
            suite_index=update.test_suite_execution_index,
        )
        if step is not None:
            title = step.title
            colored_title = colorize_hierarchy_prefix(title, HierarchyEnum.TEST_STEP.value)
            colored_state = colorize_state(update.state.value)
            click.echo(f"            - {colored_title} {colored_state}")

        # Track test step errors for later use in test case update
        if update.errors:
            case_key = (update.test_suite_execution_index, update.test_case_execution_index)
            if case_key not in self.test_case_step_errors:
                self.test_case_step_errors[case_key] = []
            self.test_case_step_errors[case_key].extend(update.errors)
            logger.debug(f"Tracked {len(update.errors)} error(s) for test case {case_key}: {update.errors}")

    def __handle_log_record(self, records: list[TestLogRecord]) -> None:
        for record in records:
            logger.log(record.level, record.message)

    def __suite(self, index: int) -> TestSuiteExecution:
        return self.run.test_suite_executions[index]

    def __case(self, index: int, suite_index: int) -> TestCaseExecution:
        suite = self.__suite(suite_index)
        return suite.test_case_executions[index]

    def __step(self, index: int, case_index: int, suite_index: int) -> TestStepExecution | None:
        case = self.__case(index=case_index, suite_index=suite_index)
        return case.test_step_executions[index]
