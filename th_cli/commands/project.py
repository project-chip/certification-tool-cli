#
# Copyright (c) 2023-2026 Project CHIP Authors
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
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import click
from pydantic import ValidationError

from th_cli.api_lib_autogen.api_client import SyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.api_lib_autogen.models import PICS, BodyImportprojectConfigApiV1ProjectsImportPost, Project, ProjectCreate, ProjectUpdate
from th_cli.client import get_client
from th_cli.colorize import (
    colorize_cmd_help,
    colorize_error,
    colorize_header,
    colorize_help,
    colorize_success,
    colorize_warning,
    italic,
)
from th_cli.exceptions import CLIError, handle_api_error, handle_file_error
from th_cli.utils import __print_config, __print_json, read_pics_config
from th_cli.validation import validate_directory_path

TABLE_FORMAT = "{:<5} {:25} {:28}"

# Click command group for project management
@click.group(
    short_help=colorize_help("Manage projects"),
    help=colorize_cmd_help("project", "Create, list, update, or delete projects"),
)
def project():
    """Manage projects - create, list, update, or delete"""
    pass


@contextmanager
def get_sync_apis(operation: str):
    client = None
    try:
        client = get_client()
        yield SyncApis(client)
    except CLIError:
        raise
    except Exception as e:
        raise CLIError(f"Unexpected error in {operation} operation: {e}")
    finally:
        if client:
            client.close()


# Click command to create a new project
@project.command(
    "create",
    short_help=colorize_help("Create a new project"),
)
@click.option(
    "--name",
    "-n",
    type=str,
    required=True,
    help=colorize_help("Name of the project"),
)
@click.option(
    "--config",
    "-c",
    type=click.Path(file_okay=True, dir_okay=False),
    help=colorize_help("Config JSON file for the project"),
)
@click.option(
    "--pics-config-folder",
    "-p",
    type=click.Path(file_okay=False, dir_okay=True),
    help=colorize_help("Directory containing PICS XML configuration files"),
)
def create(name: str, config: str | None, pics_config_folder: str | None) -> None:
    """Create a new project"""
    with get_sync_apis("create") as sync_apis:
        _create_project(sync_apis, name, config, pics_config_folder)


# Click command to list projects
@project.command(
    "list",
    short_help=colorize_help("List projects"),
)
@click.option(
    "--id",
    "-i",
    type=int,
    help=colorize_help("Project ID to retrieve a specific project"),
)
@click.option(
    "--skip",
    "-s",
    type=int,
    help=colorize_help("The first N projects to skip, ordered by ID"),
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help=colorize_help("Maximum number of projects to fetch"),
)
@click.option(
    "--archived",
    is_flag=True,
    default=False,
    help=colorize_help("List only archived projects"),
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help=colorize_help("Print JSON response for more details"),
)
@click.option(
    "--config",
    "-c",
    is_flag=True,
    default=False,
    help=colorize_help("Print project configuration in JSON format")
)
def list_projects(
    id: int | None,
    skip: int | None,
    limit: int | None,
    archived: bool,
    json: bool,
    config: bool,
) -> None:
    """List projects"""
    with get_sync_apis("list") as sync_apis:
        _list_projects(sync_apis, id, archived, skip, limit, json, config)


# Click command to update an existing project
@project.command(
    "update",
    short_help=colorize_help("Update an existing project"),
)
@click.option(
    "--id",
    "-i",
    type=int,
    required=True,
    help=colorize_help("Project ID to update"),
)
@click.option(
    "--name",
    "-n",
    type=str,
    help=colorize_help("Name of the project"),
)
@click.option(
    "--config",
    "-c",
    type=click.Path(file_okay=True, dir_okay=False),
    help=colorize_help("Config JSON file for the project"),
)
@click.option(
    "--pics-config-folder",
    "-p",
    type=click.Path(file_okay=False, dir_okay=True),
    help=colorize_help("Directory containing PICS XML configuration files"),
)
def update(id: int, config: str | None, name: str | None, pics_config_folder: str | None) -> None:
    """Update an existing project"""
    with get_sync_apis("update") as sync_apis:
        _update_project(sync_apis, id, name, config, pics_config_folder)


# Click command to delete an existing project
@project.command(
    "delete",
    short_help=colorize_help("Delete a project"),
)
@click.option(
    "--id",
    "-i",
    type=int,
    required=True,
    help=colorize_help("Project ID to delete"),
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help=colorize_help("Delete the project without confirmation"),
)
def delete(id: int, yes: bool) -> None:
    """Delete a project"""
    if not yes:
        if not click.confirm(colorize_error("Are you sure you want to delete the project?")):
            click.echo("Operation cancelled.")
            return

    with get_sync_apis("delete") as sync_apis:
        _delete_project(sync_apis, id)


# Click command to export a project config
@project.command(
    "export",
    short_help=colorize_help("Export a project config to a JSON file"),
)
@click.option(
    "--id",
    "-i",
    type=int,
    required=True,
    help=colorize_help("Project ID to export"),
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False),
    required=False,
    help=colorize_help("Output JSON file path (defaults to <project-name>-project-config.json)"),
)
def export(id: int, output_file: str | None) -> None:
    """Export a project config to a JSON file"""
    with get_sync_apis("export") as sync_apis:
        _export_project(sync_apis, id, output_file)


# Click command to import a project config from a JSON file
@project.command(
    "import",
    short_help=colorize_help("Import a project config from a JSON file"),
)
@click.option(
    "--file",
    "-f",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    required=True,
    help=colorize_help("JSON file previously exported with 'project export'"),
)
def import_project(file: str) -> None:
    """Import a project config from a JSON file"""
    with get_sync_apis("import") as sync_apis:
        _import_project(sync_apis, file)


# Click command to download all logs for a project
@project.command(
    "logs",
    short_help=colorize_help("Download all logs for a project"),
)
@click.option(
    "--id",
    "-i",
    type=int,
    required=True,
    help=colorize_help("Project ID"),
)
@click.option(
    "--grouped",
    is_flag=True,
    default=False,
    help=colorize_help(
        "Download grouped logs (organized by test case state) instead of flat log files"
    ),
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False),
    required=False,
    help=colorize_help(
        "Output zip file path (defaults to <project-name>-logs.zip)"
    ),
)
def logs(id: int, grouped: bool, output_file: str | None) -> None:
    """Download all logs for a project as a single zip archive"""
    with get_sync_apis("logs") as sync_apis:
        _download_project_logs(sync_apis, id, grouped, output_file)


def _create_project(sync_apis: SyncApis, name: str, config: str | None, pics_config_folder: str | None) -> None:
    """Create a new project"""
    # Get default config
    try:
        test_environment_config = sync_apis.projects_api.default_config_api_v1_projects_default_config_get()
    except UnexpectedResponse as e:
        handle_api_error(e, "get default config")

    # Load custom config if provided
    if config:
        try:
            with open(config, "r") as f:
                config_dict = json.load(f)
            test_environment_config = config_dict
        except FileNotFoundError as e:
            handle_file_error(e, "config file")
        except json.JSONDecodeError as e:
            raise CLIError(f"Invalid JSON in config file: {e.msg}")
        except ValidationError as e:
            raise CLIError(f"Invalid configuration: {e}")

    # Process PICS configuration if provided
    pics = PICS(clusters={})
    if pics_config_folder:
        pics_path = validate_directory_path(pics_config_folder, must_exist=True)
        pics_dict = read_pics_config(str(pics_path))
        # Convert dict to PICS model
        pics = PICS.model_validate(pics_dict)
        click.echo(colorize_success(f"Loaded PICS configuration from '{pics_config_folder}'"))

    # Create project
    project_create = ProjectCreate(name=name, config=test_environment_config, pics=pics)

    try:
        response = sync_apis.projects_api.create_project_api_v1_projects__post(body=project_create)
        click.echo(colorize_success(f"Project '{response.name}' created with ID {response.id}"))
    except UnexpectedResponse as e:
        handle_api_error(e, f"create project '{name}'")


def _list_projects(
    sync_apis: SyncApis,
    id: int | None,
    archived: bool,
    skip: int | None,
    limit: int | None,
    json: bool,
    config: bool,
) -> None:
    """List projects"""

    def __list_project_by_id(id: int) -> Project:
        try:
            return sync_apis.projects_api.read_project_api_v1_projects__id__get(id=id)
        except UnexpectedResponse as e:
            handle_api_error(e, f"list project with id '{id}'")

    def __list_project_by_batch(archived: bool, skip: int | None = None, limit: int | None = None) -> list[Project]:
        try:
            return sync_apis.projects_api.read_projects_api_v1_projects__get(archived=archived, skip=skip, limit=limit)
        except UnexpectedResponse as e:
            handle_api_error(e, "list projects")

    def __print_table(projects: Any) -> None:
        click.echo(colorize_header(TABLE_FORMAT.format("ID", "Project Name", "Updated Time")))

        if isinstance(projects, list):
            for item in projects:
                __print_project(item.model_dump())

        if isinstance(projects, Project):
            __print_project(projects.model_dump())

        click.echo(italic("\nFor more information, please use --json\n"))

    def __print_project(project: dict) -> None:
        click.echo(
            TABLE_FORMAT.format(
                project.get("id"),
                project.get("name"),
                str(project.get("updated_at")),
            )
        )

    projects: Project | list[Project]
    if id is not None:
        projects = __list_project_by_id(id)
    else:
        projects = __list_project_by_batch(archived, skip, limit)

    if projects is None or (isinstance(projects, list) and len(projects) == 0):
        raise CLIError("Server did not return any project")

    if json:
        __print_json(projects)
    elif config:
        __print_config(projects)
    else:
        __print_table(projects)


def _update_project(
    sync_apis: SyncApis,
    id: int,
    name: str | None = None,
    config_path: str | None = None,
    pics_config_folder: str | None = None,
) -> None:
    """Update an existing project"""
    try:
        if all(param is None for param in [name, config_path, pics_config_folder]):
            click.echo(colorize_warning("Nothing to be done. Please provide at least one parameter to update."))
            return

        # Get existing project to preserve its name and other fields
        existing_project = sync_apis.projects_api.read_project_api_v1_projects__id__get(id=id)

        # Use the new name, if provided
        project_name = existing_project.name
        if name:
            project_name = name
            click.echo(colorize_success(f"Project will be renamed to '{project_name}'"))

        # Load the new config if provided
        config_dict = existing_project.config
        if config_path:
            with open(config_path, "r") as f:
                config_dict = json.load(f)
                click.echo(colorize_success(f"Loaded project configuration from '{config_path}'"))

        # Process PICS configuration if provided
        pics = existing_project.pics
        if pics_config_folder:
            pics_path = validate_directory_path(pics_config_folder, must_exist=True)
            pics_dict = read_pics_config(str(pics_path))
            # Convert dict to PICS model
            pics = PICS.model_validate(pics_dict)
            click.echo(colorize_success(f"Loaded PICS configuration from '{pics_config_folder}'"))

        project_update = ProjectUpdate(
            name=project_name,
            config=config_dict,
            pics=pics,
        )

        response = sync_apis.projects_api.update_project_api_v1_projects__id__put(id=id, body=project_update)
        click.echo(colorize_success(f"Project '{response.name}' was updated."))
    except json.JSONDecodeError as e:
        raise CLIError(f"Failed to parse JSON parameter: {e.msg}")
    except FileNotFoundError as e:
        handle_file_error(e, "config file")
    except ValidationError as e:
        raise CLIError(f"Invalid configuration: {e}")
    except UnexpectedResponse as e:
        # Handle error when fetching existing project
        if "read_project" in str(e):
            handle_api_error(e, f"fetch project with ID '{id}'")
        else:
            handle_api_error(e, f"update project with '{id}'")


def _delete_project(sync_apis: SyncApis, id: int) -> None:
    """Delete a project"""
    try:
        sync_apis.projects_api.delete_project_api_v1_projects__id__delete(id=id)
        click.echo(colorize_success(f"Project {id} was deleted."))
    except UnexpectedResponse as e:
        handle_api_error(e, f"delete project ID '{id}'")


def _export_project(sync_apis: SyncApis, id: int, output_file: str | None) -> None:
    """Export a project config to a JSON file"""
    try:
        project_create: ProjectCreate = sync_apis.projects_api.export_project_config_api_v1_projects__id__export_get(
            id=id
        )
    except UnexpectedResponse as e:
        handle_api_error(e, f"export project ID '{id}'")

    if not output_file:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in (project_create.name or f"project-{id}"))
        output_file = f"{safe_name}-project-config.json"

    try:
        Path(output_file).write_text(project_create.model_dump_json(indent=2))
        click.echo(colorize_success(f"Project {id} exported to '{output_file}'"))
    except OSError as e:
        raise CLIError(f"Failed to write export file '{output_file}': {e}")


def _import_project(sync_apis: SyncApis, file: str) -> None:
    """Import a project config from a JSON file"""
    try:
        file_bytes = Path(file).read_bytes()
    except FileNotFoundError as e:
        handle_file_error(e, "import file")
    except OSError as e:
        raise CLIError(f"Failed to read import file '{file}': {e}")

    body = BodyImportprojectConfigApiV1ProjectsImportPost(import_file=file_bytes)

    try:
        response: Project = sync_apis.projects_api.importproject_config_api_v1_projects_import_post(body=body)
        click.echo(colorize_success(f"Project '{response.name}' imported with ID {response.id}"))
    except UnexpectedResponse as e:
        handle_api_error(e, f"import project from '{file}'")


def _download_project_logs(
    sync_apis: SyncApis, id: int, grouped: bool, output_file: str | None
) -> None:
    """Download all logs for a project as a single zip archive"""
    try:
        log_bytes: bytes = sync_apis.projects_api.download_project_logs_api_v1_projects__id__logs_get(
            id=id, grouped=grouped
        )
    except UnexpectedResponse as e:
        handle_api_error(e, f"download logs for project ID '{id}'")

    if not output_file:
        try:
            project = sync_apis.projects_api.read_project_api_v1_projects__id__get(id=id)
            safe_name = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in (project.name or f"project-{id}")
            )
        except Exception:
            # The logs have already been downloaded successfully at this point;
            # any failure fetching the project name (network glitch, unexpected
            # response shape, etc.) should just fall back to a safe default
            # filename instead of discarding the downloaded bytes.
            safe_name = f"project-{id}"
        output_file = f"{safe_name}-logs.zip"

    try:
        Path(output_file).write_bytes(log_bytes)
        mode = "grouped" if grouped else "flat"
        click.echo(colorize_success(f"Project {id} logs ({mode}) saved to '{output_file}'"))
    except OSError as e:
        raise CLIError(f"Failed to write logs file '{output_file}': {e}")
