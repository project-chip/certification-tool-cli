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
import click
import websockets
from loguru import logger
from pydantic import ValidationError
from websockets.client import WebSocketClientProtocol
from websockets.client import connect as websocket_connect

from th_cli.api_lib_autogen.api_client import AsyncApis
from th_cli.api_lib_autogen.models import (
    TestCaseExecution,
    TestRunExecutionWithChildren,
    TestStepExecution,
    TestSuiteExecution,
)
from th_cli.client import get_client
from th_cli.colorize import (
    HierarchyEnum,
    colorize_error,
    colorize_header,
    colorize_hierarchy_prefix,
    colorize_key_value,
    colorize_state,
)
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

WEBSOCKET_MAX_MESSAGE_SIZE = 32 * 1024 * 1024  # 32MB


class TestRunSocket:
    def __init__(
        self,
        run: TestRunExecutionWithChildren,
        project_config_dict: dict | None = None,
        two_way_talk_handler=None,
    ):
        self.run = run
        self.project_config_dict = project_config_dict or {}
        self.two_way_talk_handler = two_way_talk_handler
        self._chip_server_info_displayed = False
        # Track test step errors for logging
        # Key: (suite_index, case_index), Value: list of error strings from all steps
        self.test_case_step_errors: dict[tuple[int, int], list[str]] = {}

    async def connect_websocket(self) -> None:
        try:
            async with websocket_connect(
                WEBSOCKET_URL,
                ping_timeout=None,
                close_timeout=10,  # Allow 10 seconds for close handshake
                max_size=WEBSOCKET_MAX_MESSAGE_SIZE,
                read_limit=WEBSOCKET_MAX_MESSAGE_SIZE,
                write_limit=WEBSOCKET_MAX_MESSAGE_SIZE,
            ) as socket:
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
                            message_obj = SocketMessage.model_validate_json(message)
                            await self.__handle_incoming_socket_message(socket=socket, message=message_obj)
                        except ValidationError as e:
                            click.echo(colorize_error(f"Received invalid socket message: {message}"), err=True)
                            click.echo(colorize_error(e.json()), err=True)
                finally:
                    pass  # Cleanup if needed
        except websockets.exceptions.ConnectionClosed:
            # Handle case where backend doesn't complete close handshake properly
            # This can happen with long-running test executions
            # Error: "sent 1000 (OK); no close frame received"
            pass

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
                await handle_prompt(
                    socket=socket,
                    request=message.payload,
                    message_type=message.type,
                    two_way_talk_handler=self.two_way_talk_handler,
                )
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
            await self.__log_test_run_update(update.body)
            if update.body.state != "executing":
                # Test run ended disconnect.
                try:
                    await socket.close()
                except websockets.exceptions.ConnectionClosedError:
                    # Backend closed connection without completing handshake
                    # This is acceptable as test run completed successfully
                    pass

    async def __log_test_run_update(self, update: TestRunUpdate) -> None:
        # Display CHIP server info when test run starts executing (SDK container already running)
        if update.state.value == "executing" and not self._chip_server_info_displayed:
            await self.__display_manual_pairing_code()
            self._chip_server_info_displayed = True

        test_run_text = colorize_hierarchy_prefix("Test Run", HierarchyEnum.TEST_RUN.value)
        colored_state = colorize_state(update.state.value)
        click.echo(f"{test_run_text} {colored_state}")

    async def __display_manual_pairing_code(self) -> None:
        """Fetch and display manual pairing code after SDK container has started."""
        try:
            # Extract device configuration
            dut_config = self.project_config_dict.get("dut_config", {})
            discriminator = dut_config.get("discriminator")
            setup_pin_code = dut_config.get("setup_code")

            if not discriminator or not setup_pin_code:
                return  # No device config available

            # Extract version, vendor_id and product_id from test_parameters if available
            test_parameters = self.project_config_dict.get("test_parameters", {})
            version = test_parameters.get("version") if test_parameters else None
            vendor_id = test_parameters.get("vendor_id") if test_parameters else None
            product_id = test_parameters.get("product_id") if test_parameters else None

            # Create API client and fetch chip server info
            client = get_client()
            try:
                test_run_api = AsyncApis(client).test_run_executions_api
                chip_info = await test_run_api.get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
                    discriminator=discriminator,
                    setup_pin_code=setup_pin_code,
                    version=version,
                    vendor_id=vendor_id,
                    product_id=product_id,
                )

                node_id = colorize_key_value("Node ID", chip_info.node_id_hex)
                click.echo("═══════════════════════════════════════════════════════")
                click.echo(colorize_header("CHIP Server Information:"))
                click.echo(f"- {node_id}")
                if chip_info.manual_pairing_code:
                    manual_code = colorize_key_value("Manual Pairing Code", chip_info.manual_pairing_code)
                    click.echo(f"- {manual_code}")
                click.echo("═══════════════════════════════════════════════════════")
                click.echo("")
            finally:
                await client.aclose()

        except Exception as e:
            logger.debug(f"Could not fetch manual pairing code: {e}")
            # Don't fail the test run if we can't get the pairing code

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

        # Log any errors when a test case fails
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
                    f"Found {len(self.test_case_step_errors[case_key])} tracked step error(s): "
                    f"{self.test_case_step_errors[case_key]}"
                )
            else:
                logger.debug(f"No tracked step errors found for test case {case_key}")

            # Check if a WebRTC test failed because the browser peer connection was unavailable.
            # Two-way talk tests uses the TH browser tab as a WebRTC client — the browser must be
            # open with the TH UI for the test to work.
            if all_errors:
                error_text = " ".join(all_errors).lower()
                browser_peer_errors = ["peer not found", "browserpeerconnection", "create_browser_peer"]
                if any(indicator in error_text for indicator in browser_peer_errors):
                    click.echo("")
                    click.echo(colorize_error("⚠️  BROWSER TAB REQUIRED"), err=True)
                    click.echo(colorize_error(f"   {title} requires the TH browser UI to be open."), err=True)
                    click.echo(colorize_error("   Open the TH web interface in a browser tab and re-run."), err=True)
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
            self.test_case_step_errors.setdefault(case_key, []).extend(update.errors)
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
