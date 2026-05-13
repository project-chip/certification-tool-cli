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
from contextlib import closing

import click

from th_cli.api_lib_autogen.api_client import SyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.client import get_client
from th_cli.colorize import colorize_cmd_help, colorize_header, colorize_help, colorize_state, italic
from th_cli.exceptions import CLIError, handle_api_error
from th_cli.utils import __print_json

table_format_header = "{:<6} {:<55} {}"
table_format = "{:<6} {} {}"

_list_options = [
    click.option(
        "--id",
        "-i",
        default=None,
        required=False,
        type=int,
        help=colorize_help("Fetch specific Test Run via ID"),
    ),
    click.option(
        "--skip",
        "-s",
        default=None,
        required=False,
        type=int,
        help=colorize_help("The first N Test Runs to skip, ordered by ID"),
    ),
    click.option(
        "--limit",
        "-l",
        default=None,
        required=False,
        type=int,
        help=colorize_help("Maximum number of test runs to fetch (default: 100)"),
    ),
    click.option(
        "--sort",
        default="desc",
        required=False,
        type=click.Choice(["asc", "desc"], case_sensitive=False),
        help=colorize_help(
            "Sort order for test runs by ID. 'desc' shows highest ID first, 'asc' shows lowest ID first"
        ),
    ),
    click.option(
        "--project-id",
        "-p",
        default=None,
        required=False,
        type=int,
        help=colorize_help("Filter test runs by project ID"),
    ),
    click.option(
        "--log",
        is_flag=True,
        default=False,
        help=colorize_help("Fetch log content for the specified test run execution ID (requires --id)"),
        deprecated="Use the log command",
    ),
    click.option(
        "--json",
        is_flag=True,
        default=False,
        help=colorize_help("Print JSON response for more details (not applicable with --log)"),
    ),
    click.option(
        "--all",
        is_flag=True,
        default=False,
        help=colorize_help("Fetch all test run executions with screen pagination (cannot be used with --limit)"),
    ),
]


def add_options(options):
    def _add_options(func):
        for option in reversed(options):  # reversed preserves order
            func = option(func)
        return func

    return _add_options


@click.group(
    short_help=colorize_help("Manage test run executions"),
    help=colorize_cmd_help(
        "test_run_execution", "List test run execution history or fetch logs for a specific execution"
    ),
    invoke_without_command=True,
)
@click.pass_context
# For the sake of backwards-compatibility, these arguments are applied to both the base command
# as well as the list command
@add_options(_list_options)
def test_run_execution(
    ctx,
    id: int | None,
    skip: int | None,
    limit: int | None,
    sort: str,
    project_id: int | None,
    log: bool,
    json: bool,
    all: bool,
) -> None:
    """Manage test run executions - list history or fetch logs"""
    if ctx.invoked_subcommand is None:
        ctx.forward(list_executions)


@test_run_execution.command(
    name="list",
    short_help=colorize_help("List test run executions"),
    help=colorize_cmd_help("list", "List test run execution history"),
)
@add_options(_list_options)
def list_executions(
    id: int | None,
    skip: int | None,
    limit: int | None,
    sort: str,
    project_id: int | None,
    log: bool,
    json: bool,
    all: bool,
) -> None:
    """Manage test run executions - list history or fetch logs"""

    # Validate options
    if log and (skip is not None or limit is not None or project_id is not None):
        raise click.ClickException(
            "--skip, --limit, and --project-id options are not applicable when fetching logs (--log)"
        )

    if log and id is None:
        raise click.ClickException("--log requires --id to specify which test run execution to fetch logs for")

    if log and json:
        raise click.ClickException("--json option is not applicable when fetching logs (--log)")

    if log and sort != "desc":
        raise click.ClickException("--sort option is not applicable when fetching logs (--log)")

    if all and limit is not None:
        raise click.ClickException("--all and --limit cannot be used together")

    if log and all:
        raise click.ClickException("--all option is not applicable when fetching logs (--log)")

    try:
        with closing(get_client()) as client:
            sync_apis = SyncApis(client)

            if log:
                __fetch_test_run_execution_log(sync_apis, id, None)
            elif id is not None:
                __test_run_execution_by_id(sync_apis, id, json)
            else:
                __test_run_execution_batch(sync_apis, json, skip, limit, sort, all, project_id)

    except CLIError:
        raise  # Re-raise CLI Errors as-is


@test_run_execution.command(
    short_help=colorize_help("Fetch test run execution logs"),
    help=colorize_cmd_help("log", "Fetch logs for a specific execution"),
)
@click.option(
    "--id",
    "-i",
    required=True,
    type=int,
    help=colorize_help("Fetch specific Test Run logs via ID"),
)
@click.option(
    "--output-file",
    "-o",
    required=False,
    type=str,
    help=colorize_help("Output file. Test run execution title will be used by default"),
)
@click.option(
    "--grouped",
    is_flag=True,
    default=False,
    help=colorize_help("Download a zip archive of the grouped logs"),
)
def log(id: int, output_file: str, grouped: bool) -> None:
    try:
        with closing(get_client()) as client:
            sync_apis = SyncApis(client)

            if grouped:
                __fetch_grouped_test_run_execution_log(sync_apis, id, output_file)
            else:
                __fetch_test_run_execution_log(sync_apis, id, output_file)

    except CLIError:
        raise  # Re-raise CLI Errors as-is


def __test_run_execution_by_id(sync_apis: SyncApis, id: int, json: bool) -> None:
    try:
        test_run_execution_api = sync_apis.test_run_executions_api
        test_run_execution = test_run_execution_api.read_test_run_execution_api_v1_test_run_executions__id__get(id=id)
        if json:
            __print_json(test_run_execution)
        else:
            __print_table_test_execution(test_run_execution.model_dump())
    except UnexpectedResponse as e:
        handle_api_error(e, "get test run execution")


def __print_filters_info(
    skip: int | None, limit: int | None, sort_order: str, show_all: bool = False, project_id: int | None = None
) -> str:
    """Generate comprehensive filter and pagination information text."""
    filters = []

    # Project filter
    if project_id is not None:
        filters.append(f"Project ID: {project_id}")

    # Order information (more descriptive than just "Sort: DESC")
    if sort_order == "desc":
        filters.append("Order: newest first")
    else:
        filters.append("Order: oldest first")

    # Pagination info
    if show_all:
        filters.append("Results: ALL RECORDS")
    else:
        # Skip info
        if skip is not None:
            filters.append(f"Skip: {skip}")
        else:
            filters.append("Skip: 0 (from start)")

        # Limit info
        if limit is not None:
            filters.append(f"Limit: {limit}")
        else:
            filters.append("Limit: 100 (default)")

    return f"🔍 Active Filters: {' • '.join(filters)}"


def __test_run_execution_batch(
    sync_apis: SyncApis,
    json: bool | None,
    skip: int | None = None,
    limit: int | None = None,
    sort_order: str = "desc",
    show_all: bool = False,
    project_id: int | None = None,
) -> None:
    try:
        test_run_execution_api = sync_apis.test_run_executions_api

        # When --all is used, set limit to 0 to get all results
        effective_limit = 0 if show_all else limit

        test_run_executions = test_run_execution_api.read_test_run_executions_api_v1_test_run_executions__get(
            skip=skip, limit=effective_limit, sort_order=sort_order, project_id=project_id
        )

        if json:
            __print_json(test_run_executions)
        else:
            if show_all:
                # Use click's pager for --all option (like git log)
                output_lines = []
                output_lines.append(
                    click.style(
                        __print_filters_info(skip, limit, sort_order, show_all, project_id), fg="cyan", bold=True
                    )
                )
                output_lines.append("")  # Empty line

                # Add header
                output_lines.append(colorize_header(table_format_header.format("ID", "Title", "State")))

                # Add all test executions
                if isinstance(test_run_executions, list):
                    for item in test_run_executions:
                        # Get raw values to calculate proper padding
                        title_value = item.title

                        # Apply styling
                        styled_title = italic(title_value)

                        # Calculate padding needed for title (55 chars total)
                        title_padding = max(0, 55 - len(title_value))

                        output_lines.append(
                            table_format.format(
                                item.id,
                                styled_title,
                                " " * title_padding,
                            )
                            + colorize_state((item.state).value)
                        )

                # Use pager to display all content
                click.echo_via_pager("\n".join(output_lines))
            else:
                # Regular output with filter info
                click.echo(
                    click.style(
                        __print_filters_info(skip, limit, sort_order, show_all, project_id), fg="cyan", bold=True
                    )
                )
                click.echo()  # Add empty line for readability
                __print_table_test_executions(test_run_executions)
    except UnexpectedResponse as e:
        handle_api_error(e, "get test run executions")


def __fetch_test_run_execution_log(sync_apis: SyncApis, id: int, output_file: str | None) -> None:
    try:
        test_run_execution_api = sync_apis.test_run_executions_api
        log_content = test_run_execution_api.download_log_api_v1_test_run_executions__id__log_get(
            id=id, json_entries=False, download=False
        )

        if log_content:
            if output_file:
                with open(output_file, "w", encoding="utf-8") as outfile:
                    outfile.write(log_content)
            else:
                click.echo(log_content)
        else:
            click.echo("No log content available for this test run execution.")

    except UnexpectedResponse as e:
        handle_api_error(e, "fetch test run execution log")


def __fetch_grouped_test_run_execution_log(sync_apis: SyncApis, id: int, output_file: str | None) -> None:
    try:
        test_run_execution_api = sync_apis.test_run_executions_api
        log_content = test_run_execution_api.download_grouped_log_api_v1_test_run_executions__id__grouped_log_get(id=id)

        if log_content:
            if not output_file:
                execution_data = test_run_execution_api.read_test_run_execution_api_v1_test_run_executions__id__get(
                    id=id
                )
                if execution_data:
                    import re

                    output_file = re.sub(r"[^\w]", "", execution_data.title) + ".zip"
                else:
                    output_file = f"test_run_execution_{id}_grouped.zip"

            with open(output_file, "wb") as outfile:
                outfile.write(log_content)

        else:
            click.echo("No log content available for this test run execution.")

    except UnexpectedResponse as e:
        handle_api_error(e, "fetch grouped test run execution log")


def __print_table_test_executions(test_execution: list) -> None:
    __print_table_header()
    if isinstance(test_execution, list):
        for item_dict in test_execution:
            __print_table_test_execution(item_dict.model_dump(), print_header=False)


def __print_table_test_execution(item: dict, print_header=True) -> None:
    print_header and __print_table_header()

    # Get raw values to calculate proper padding
    title_value = item.get("title")

    # Apply styling
    styled_title = italic(title_value)

    # Calculate padding needed for title (55 chars total)
    title_padding = max(0, 55 - len(title_value))

    click.echo(
        table_format.format(
            item.get("id"),
            styled_title,
            " " * title_padding,
        )
        + colorize_state((item.get("state")).value)
    )


def __print_table_header() -> None:
    click.echo(colorize_header(table_format_header.format("ID", "Title", "State")))
