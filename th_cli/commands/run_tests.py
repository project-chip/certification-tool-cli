#
# Copyright (c) 2025-2026 Project CHIP Authors
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
import copy
import datetime
import json
import socket as _socket
from typing import Any

import click

import th_cli.api_lib_autogen.models as m
import th_cli.test_run.camera.two_way_talk_handler as _twt_mod
import th_cli.test_run.logging as test_logging
from th_cli.api_lib_autogen.api_client import AsyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.async_cmd import async_cmd
from th_cli.client import get_client
from th_cli.colorize import (
    colorize_cmd_help,
    colorize_header,
    colorize_help,
    colorize_key_value,
    colorize_warning,
    italic,
    set_colors_enabled,
)
from th_cli.config import config as th_config
from th_cli.exceptions import CLIError, handle_api_error
from th_cli.test_run.camera.two_way_talk_handler import TwoWayTalkHandler
from th_cli.test_run.websocket import TestRunSocket
from th_cli.utils import DEFAULT_CLI_PROJECT_NAME, build_test_selection, convert_nested_to_dict, load_json_config, merge_configs, read_pics_config
from th_cli.validation import validate_directory_path, validate_file_path, validate_test_ids

# Constants
JSON_INDENT = 2

# Test cases that require the two-way talk browser verification server.
TWO_WAY_TALK_TEST_IDS: frozenset[str] = frozenset({"TC_WEBRTC_1_6"})


@click.command(
    no_args_is_help=True,
    short_help=colorize_help("CLI execution of a test run"),
    help=colorize_cmd_help("run_tests", "CLI execution of a test run from selected tests"),
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--tests-list",
    "-t",
    required=True,
    help=colorize_help("List of test cases to execute. For example: TC-ACE-1.1,TC_ACE_1_3"),
)
@click.option(
    "--title",
    "-n",
    default=lambda: str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")),
    show_default="timestamp",
    help=colorize_help("Name of the test run execution"),
)
@click.option(
    "--config",
    "-c",
    type=click.Path(file_okay=True, dir_okay=False),
    help=colorize_help(
        "JSON config file location. If not provided, the project's default " "configuration will be used."
    ),
)
@click.option(
    "--pics-config-folder",
    "-p",
    type=click.Path(file_okay=False, dir_okay=True),
    help=colorize_help("Directory containing PICS XML configuration files. If not provided, no PICS will be used."),
)
@click.option(
    "--project-id",
    type=int,
    help=colorize_help(
        "Project ID that this test run belongs to. " "If not provided, uses the default 'CLI Execution Project' in TH."
    ),
)
@click.option(
    "--no-color",
    is_flag=True,
    help=colorize_help("Disable colored output for test execution status."),
)
@async_cmd
@click.pass_context
async def run_tests(
    ctx: click.Context,
    title: str,
    tests_list: str,
    config: str | None = None,
    pics_config_folder: str | None = None,
    project_id: int | None = None,
    no_color: bool = False,
) -> None:
    """Execute a CLI test run from selected test cases.

    Args:
        ctx: Click context containing extra arguments
        title: Name/title for the test run execution
        tests_list: Comma-separated list of test case identifiers
        config: Optional path to JSON configuration file
        pics_config_folder: Optional path to directory containing PICS XML files
        project_id: Optional project ID for the test run
        no_color: Flag to disable colored output

    Raises:
        CLIError: If there are validation or execution errors
    """
    # Extract and parse extra arguments from context (args after --)
    extra_test_params = _parse_extra_args(list(ctx.args)) if ctx.args else {}

    # Set color preference if specified
    if no_color:
        set_colors_enabled(False)

    # Validate inputs and convert each test separated by comma to a list
    validated_test_ids = validate_test_ids(tests_list)

    if config:
        config_path = validate_file_path(config, must_exist=True)
        config = str(config_path)

    if pics_config_folder:
        pics_path = validate_directory_path(pics_config_folder, must_exist=True)
        pics_config_folder = str(pics_path)

    client = None
    _webrtc_handler = None
    try:
        client = get_client()
        async_apis = AsyncApis(client)
        test_collections_api = async_apis.test_collections_api

        # Configure new log output for test.
        log_path = test_logging.configure_logger_for_run(title=title)

        # Retrieve CLI project
        cli_project = await _get_cli_project(async_apis, project_id)

        # Get project config and convert to dict
        project_config = await _get_project_config(async_apis, cli_project)
        project_config_dict = convert_nested_to_dict(project_config)

        # Create execution config. If a config file is provided, merge it with the
        # project config. Otherwise, just use a copy of the project config.
        # This avoids modifying the original project_config_dict.
        if config:
            config_data = load_json_config(config)
            test_run_config = merge_configs(project_config_dict, config_data)
            click.echo(colorize_key_value("Config Used (Execution Only)", test_run_config))
        else:
            test_run_config = copy.deepcopy(project_config_dict)
            click.echo(colorize_key_value("Config Used (From Project)", project_config_dict))

        # Read PICS configuration if provided via CLI (execution-only, not persisted)
        # Otherwise use PICS from project (persistent)
        execution_pics: dict[str, Any] | None = None
        if pics_config_folder:
            execution_pics = read_pics_config(pics_config_folder)
            click.echo(colorize_key_value("PICS Used (Execution Only)", json.dumps(execution_pics, indent=JSON_INDENT)))
        else:
            execution_pics = await _get_project_pics(cli_project)
            click.echo(colorize_key_value("PICS Used (From Project)", json.dumps(execution_pics, indent=JSON_INDENT)))

        # Merge extra test parameters if provided (temporary for this execution only)
        if extra_test_params:
            click.echo(
                colorize_key_value(
                    "Extra SDK Test Parameters (Execution Only)", json.dumps(extra_test_params, indent=JSON_INDENT)
                )
            )
            if "test_parameters" not in test_run_config or test_run_config["test_parameters"] is None:
                test_run_config["test_parameters"] = {}
            test_run_config["test_parameters"].update(extra_test_params)

        # Retrieve available test collections to build test selection
        test_collections = await test_collections_api.read_test_collections_api_v1_test_collections__get()
        selected_tests_dict = build_test_selection(test_collections, validated_test_ids)

        click.echo(colorize_key_value("Selected tests", json.dumps(selected_tests_dict, indent=JSON_INDENT)))

        new_test_run = await _create_new_test_run_cli(
            async_apis,
            selected_tests=selected_tests_dict,
            title=title,
            execution_config=test_run_config,
            execution_pics=execution_pics,
            project_id=project_id,
        )
        if _contains_webrtc_two_way_talk(selected_tests_dict):
            _webrtc_handler = TwoWayTalkHandler(port=8999)
            _webrtc_handler.start_waiting()
            await _print_webrtc_banner_and_wait(th_config.hostname, _webrtc_handler)
        else:
            _webrtc_handler = None
        socket = TestRunSocket(new_test_run, test_run_config, two_way_talk_handler=_webrtc_handler)
        socket_task = asyncio.create_task(socket.connect_websocket())
        new_test_run = await _start_test_run(async_apis, new_test_run)
        socket.run = new_test_run
        await socket_task
        click.echo(colorize_key_value("Log output in", italic(log_path)))
    except CLIError:
        raise  # Re-raise CLI errors
    except Exception as e:
        raise CLIError(f"Unexpected error during test execution: {e}")
    finally:
        if client:
            await client.aclose()
        if _webrtc_handler:
            _webrtc_handler.stop()


async def _get_cli_project(async_apis: AsyncApis, project_id: int | None = None) -> m.Project:
    """Retrieve the project to use for the CLI test run execution.
    Args:
        async_apis: AsyncApis instance for making API calls
        project_id: Optional project ID to retrieve. If None, retrieves the default CLI project.
    Returns:
        Project object to use for the test run execution
    Raises:
        CLIError: If the specified project ID does not exist or if the default CLI project cannot be found
    """
    projects_api = async_apis.projects_api

    if project_id is not None:
        try:
            return await projects_api.read_project_api_v1_projects__id__get(id=project_id)
        except UnexpectedResponse as e:
            raise CLIError(f"Could not retrieve project with ID '{project_id}': {e}")

    # If no project ID provided, search for the default CLI project by name
    try:
        projects = await projects_api.read_projects_api_v1_projects__get(skip=0, limit=None)
        for project in projects:
            if project.name == DEFAULT_CLI_PROJECT_NAME:
                return project
    except UnexpectedResponse as e:
        click.echo(colorize_warning(f"Warning: Could not retrieve CLI default project: {e}"))

    return None


async def _get_project_config(async_apis: AsyncApis, cli_project: m.Project | None = None) -> dict[str, Any]:
    """Retrieve project configuration for given project ID or default configuration.

    Args:
        async_apis: AsyncApis instance for making API calls
        cli_project: Optional CLI project object to retrieve the project configuration

    Returns:
        Dictionary containing project configuration

    Raises:
        May raise API-related exceptions if default config retrieval fails
    """
    try:
        if cli_project is not None and cli_project.config is not None:
            return cli_project.config
    except UnexpectedResponse as e:
        msg = (
            f"Could not retrieve configuration for project ID '{cli_project.id}': {e}"
            "Falling back to default configuration."
        )
        click.echo(colorize_warning(f"Warning: {msg}"))

    projects_api = async_apis.projects_api
    return await projects_api.default_config_api_v1_projects_default_config_get()


async def _get_project_pics(cli_project: m.Project | None = None) -> dict[str, Any]:
    """Retrieve project PICS for given project ID.

    Args:
        async_apis: AsyncApis instance for making API calls
        cli_project: Optional CLI project object to retrieve PICS from

    Returns:
        Dictionary containing project PICS, or empty PICS dict if no project or PICS found

    Raises:
        May raise API-related exceptions if project retrieval fails
    """
    try:
        # Convert PICS model to dict if it exists, otherwise return empty PICS
        if cli_project is not None and cli_project.pics is not None:
            return convert_nested_to_dict(cli_project.pics)
    except UnexpectedResponse as e:
        click.echo(colorize_warning(f"Warning: Could not retrieve PICS for project ID '{cli_project.id}': {e}"))
    return {"clusters": {}}


def _contains_webrtc_two_way_talk(selected_tests: dict[str, Any]) -> bool:
    """Return True if any two-way talk test is among the selected tests."""
    return any(_dict_contains_key(selected_tests, tc) for tc in TWO_WAY_TALK_TEST_IDS)


def _dict_contains_key(d: Any, target: str) -> bool:
    """Recursively search a nested dict for a specific key."""
    if isinstance(d, dict):
        if target in d:
            return True
        return any(_dict_contains_key(v, target) for v in d.values())
    return False


async def _print_webrtc_banner_and_wait(hostname: str, handler: Any) -> None:
    """Print a prominent banner for two-way talk tests and wait until the browser opens the page."""
    # Resolve to actual LAN IP if hostname resolves to any loopback address
    try:
        resolved = _socket.gethostbyname(hostname)
    except _socket.gaierror:
        resolved = hostname
    if resolved.startswith("127.") or resolved == "::1":
        hostname = _twt_mod._get_local_ip()

    url = f"http://{hostname}:8999"
    border = click.style("═" * 57, fg="yellow", bold=True)
    click.echo(border)
    click.echo(click.style("  ⚠  WebRTC Two-Way Talk — Action Required  ⚠", fg="yellow", bold=True))
    click.echo(border)
    click.echo(click.style("  Open this URL in a browser NOW and keep it open:", fg="bright_white", bold=True))
    click.echo("  " + click.style(f"{url}", fg="cyan", bold=True, underline=True))
    click.echo(click.style("  The page will connect to the DUT automatically.", fg="bright_white"))
    click.echo(click.style("  You will be asked to select PASS or FAIL during the test.", fg="bright_white"))
    click.echo(border)
    click.echo("")

    click.echo(click.style("  Waiting for browser to open the page...", fg="yellow"))
    connected = await asyncio.get_event_loop().run_in_executor(None, handler.wait_for_browser, 120.0)
    if connected:
        click.echo(click.style("  ✔ Browser connected — starting test.", fg="green", bold=True))
    else:
        click.echo(click.style("  ⚠ Browser not detected — proceeding anyway.", fg="yellow", bold=True))
    click.echo("")


def _parse_extra_args(args: list[str]) -> dict[str, str]:
    """Parse extra arguments from -- separator into test_parameters format.

    Converts arguments as ['--int-arg', 'some-arg:2', '--bool-arg', 'flag:true']
    into {'int-arg': 'some-arg:2', 'bool-arg': 'flag:true'}

    Args:
        args: List of arguments after the -- separator

    Returns:
        Dictionary of parameter name to value mappings
    """
    params: dict[str, str] = {}
    i = 0

    while i < len(args):
        arg = args[i]

        # Skip non-flag arguments or subsequent --
        if not arg.startswith("-") or arg == "--":
            i += 1
            continue

        # Extract parameter name (remove leading dashes)
        if arg.startswith("--"):
            param_name = arg[2:]
        else:
            param_name = arg[1:]

        # Check if next argument exists and is a value (not a flag)
        has_value = i + 1 < len(args) and not args[i + 1].startswith("-")

        if has_value:
            params[param_name] = args[i + 1]
            i += 2  # Skip both parameter and value
        else:
            # Flag without value (e.g., --verbose)
            params[param_name] = ""
            i += 1

    return params


async def _create_new_test_run_cli(
    async_apis: AsyncApis,
    selected_tests: dict[str, Any],
    title: str,
    execution_config: dict[str, Any] | None = None,
    execution_pics: dict[str, Any] | None = None,
    project_id: int | None = None,
) -> m.TestRunExecutionWithChildren:
    """Create a new test run execution via the CLI.

    Args:
        async_apis: AsyncApis instance for making API calls
        selected_tests: Dictionary of selected test cases
        title: Title for the test run
        execution_config: Optional execution-specific configuration (temporary)
        execution_pics: Optional execution-specific PICS (temporary)
        project_id: Optional project ID

    Returns:
        Created TestRunExecutionWithChildren object

    Raises:
        CLIError: If test run creation fails
    """
    click.echo(colorize_key_value("Creating new test run with title", title))

    test_run_in = m.TestRunExecutionCreate(title=title, project_id=project_id)
    json_body = m.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost(
        test_run_execution_in=test_run_in,
        selected_tests=selected_tests,
        execution_config=execution_config,
        execution_pics=execution_pics,
        certification_mode=False,
    )

    try:
        test_run_executions_api = async_apis.test_run_executions_api
        return await test_run_executions_api.create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
            json_body
        )
    except UnexpectedResponse as e:
        handle_api_error(e, "create test run execution")


async def _start_test_run(
    async_apis: AsyncApis, test_run: m.TestRunExecutionWithChildren
) -> m.TestRunExecutionWithChildren:
    """Start a test run execution.

    Args:
        async_apis: AsyncApis instance for making API calls
        test_run: TestRunExecutionWithChildren object to start

    Returns:
        Updated TestRunExecutionWithChildren object after starting

    Raises:
        CLIError: If test run start fails
    """
    test_run_executions_api = async_apis.test_run_executions_api
    header = colorize_header("Starting Test run")
    title = colorize_key_value("Title", test_run.title)
    test_run_id = colorize_key_value("ID", str(test_run.id))

    click.echo("")
    click.echo(f"{header}:\n- {title}\n- {test_run_id}\n")

    try:
        return await test_run_executions_api.start_test_run_execution_api_v1_test_run_executions__id__start_post(
            id=test_run.id
        )
    except UnexpectedResponse as e:
        handle_api_error(e, "start test run")
