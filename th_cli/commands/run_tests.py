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
from typing import Any

import click

import th_cli.api_lib_autogen.models as m
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
    italic,
    set_colors_enabled,
)
from th_cli.exceptions import CLIError, handle_api_error
from th_cli.test_run.websocket import TestRunSocket
from th_cli.utils import build_test_selection, convert_nested_to_dict, load_json_config, merge_configs, read_pics_config
from th_cli.validation import validate_directory_path, validate_file_path, validate_test_ids

# Constants
JSON_INDENT = 2


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
    try:
        client = get_client()
        async_apis = AsyncApis(client)
        test_collections_api = async_apis.test_collections_api

        # Configure new log output for test.
        log_path = test_logging.configure_logger_for_run(title=title)

        # Get project config and convert to dict
        project_config = await _get_project_config(async_apis, project_id)
        project_config_dict = convert_nested_to_dict(project_config)
        click.echo(colorize_key_value("Project Config", project_config_dict))

        # If config file is provided, read JSON config and merge into project config
        if config:
            config_data = load_json_config(config)
            project_config_dict = merge_configs(project_config_dict, config_data)
            click.echo(colorize_key_value("CLI Test Run Execution Config", project_config_dict))

        # Create a DEEP copy for this test run execution to avoid modifying the original
        # This ensures extra parameters only apply to THIS run, not future runs
        test_run_config = copy.deepcopy(project_config_dict)

        # Merge extra test parameters if provided (temporary for this execution only)
        if extra_test_params:
            click.echo(
                colorize_key_value(
                    "Extra SDK Test Parameters (This Run Only)", json.dumps(extra_test_params, indent=JSON_INDENT)
                )
            )
            if "test_parameters" not in test_run_config or test_run_config["test_parameters"] is None:
                test_run_config["test_parameters"] = {}
            test_run_config["test_parameters"].update(extra_test_params)

        # Read PICS configuration if provided
        pics = read_pics_config(pics_config_folder)
        click.echo(colorize_key_value("PICS Used", json.dumps(pics, indent=JSON_INDENT)))

        # Retrieve available test collections to build test selection
        test_collections = await test_collections_api.read_test_collections_api_v1_test_collections__get()
        selected_tests_dict = build_test_selection(test_collections, validated_test_ids)

        click.echo(colorize_key_value("Selected tests", json.dumps(selected_tests_dict, indent=JSON_INDENT)))

        new_test_run = await _create_new_test_run_cli(
            async_apis,
            selected_tests=selected_tests_dict,
            title=title,
            config=project_config_dict,
            execution_config=test_run_config,
            pics=pics,
            project_id=project_id,
        )
        socket = TestRunSocket(new_test_run, test_run_config)
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


async def _get_project_config(async_apis: AsyncApis, project_id: int | None = None) -> dict[str, Any]:
    """Retrieve project configuration for given project ID or default configuration.

    Args:
        async_apis: AsyncApis instance for making API calls
        project_id: Optional project ID to retrieve configuration from

    Returns:
        Dictionary containing project configuration

    Raises:
        May raise API-related exceptions if default config retrieval fails
    """
    projects_api = async_apis.projects_api

    if project_id is not None:
        try:
            project = await projects_api.read_project_api_v1_projects__id__get(id=project_id)
            return project.config
        except UnexpectedResponse as e:
            msg = (
                f"Could not retrieve configuration for project ID '{project_id}': {e}"
                "Falling back to default configuration."
            )
            click.echo(colorize_key_value("Warning:", msg))

    return await projects_api.default_config_api_v1_projects_default_config_get()


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
    config: dict[str, Any] | None = None,
    execution_config: dict[str, Any] | None = None,
    pics: dict[str, Any] | None = None,
    project_id: int | None = None,
) -> m.TestRunExecutionWithChildren:
    """Create a new test run execution via the CLI.

    Args:
        async_apis: AsyncApis instance for making API calls
        selected_tests: Dictionary of selected test cases
        title: Title for the test run
        config: Optional configuration that updates project (persistent)
        execution_config: Optional execution-specific configuration (temporary)
        pics: Optional PICS configuration dictionary
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
        config=config,
        execution_config=execution_config,
        pics=pics,
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
