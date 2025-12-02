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

from .camera.webrtc_session import CLIWebRTCSession
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
        self.webrtc_session = None  # Will be initialized during connection
        self.webrtc_task = None  # Background task for WebRTC connection

    async def connect_websocket(self) -> None:

        async with websocket_connect(WEBSOCKET_URL, ping_timeout=None) as socket:
            # Initialize WebRTC peer connection for camera tests
            # This must happen BEFORE tests start, so the peer is available when tests need it
            await self._initialize_webrtc_peer()

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
                # Clean up WebRTC session when test run ends
                await self._cleanup_webrtc_peer()

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

    async def _initialize_webrtc_peer(self) -> None:
        """Initialize WebRTC peer connection for camera tests.

        This connects the CLI as a WebRTC peer so camera/video tests can use it
        instead of requiring the frontend browser.
        """
        try:
            logger.info("Initializing WebRTC peer connection for camera tests...")
            self.webrtc_session = CLIWebRTCSession()

            # Connect in background so it doesn't block test execution
            # Some tests may not need WebRTC, so we continue even if it fails
            connected = await self.webrtc_session.connect()

            if connected:
                logger.info("✅ WebRTC peer connection established - CLI ready for camera tests")
                click.echo("✅ WebRTC peer connected - ready for camera tests")
            else:
                logger.warning("⚠️  WebRTC peer connection failed - camera tests may not work")
                click.echo("⚠️  WebRTC peer connection failed - camera tests may not work")
                self.webrtc_session = None

        except Exception as e:
            logger.warning(f"Failed to initialize WebRTC peer: {e}")
            logger.warning("Camera tests requiring WebRTC peer may fail")
            click.echo(f"⚠️  WebRTC initialization warning: {e}")
            self.webrtc_session = None

    async def _cleanup_webrtc_peer(self) -> None:
        """Clean up WebRTC peer connection when test run ends."""
        if self.webrtc_session:
            try:
                logger.info("Closing WebRTC peer connection...")
                await self.webrtc_session.close()
                logger.info("WebRTC peer connection closed")
            except Exception as e:
                logger.warning(f"Error closing WebRTC peer: {e}")
            finally:
                self.webrtc_session = None

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
        colored_title = colorize_hierarchy_prefix(title, HierarchyEnum.TEST_CASE.value)
        colored_state = colorize_state(update.state.value)
        click.echo(f"      - {colored_title} {colored_state}")

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
