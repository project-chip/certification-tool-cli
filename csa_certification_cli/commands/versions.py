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
import os
import subprocess

import click
import tomli

from csa_certification_cli.api_lib_autogen.api_client import SyncApis
from csa_certification_cli.api_lib_autogen.exceptions import UnexpectedResponse
from csa_certification_cli.client import get_client
from csa_certification_cli.config import PROJECT_ROOT
from csa_certification_cli.exceptions import handle_api_error, handle_file_error


def get_cli_version() -> str:
    """Get CLI version from pyproject.toml"""
    try:
        pyproject_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        if os.path.exists(pyproject_path):
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomli.load(f)
                version = pyproject_data.get("project", {}).get("version")
                if version:
                    return version
        return "unknown"
    except FileNotFoundError as e:
        handle_file_error(e, f"{pyproject_path} file")
    except IOError:
        return "unknown"


def _get_cli_sha() -> str:
    """Get current CLI SHA from git"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        return result.stdout.strip()[:8]
    except FileNotFoundError as e:
        handle_file_error(e, f"{PROJECT_ROOT} directory")
    except subprocess.CalledProcessError:
        return "unknown"


@click.command()
def versions() -> None:
    """Get application versions information"""
    client = None
    try:
        client = get_client()
        sync_apis = SyncApis(client)
        versions_api = sync_apis.versions_api

        versions_info = versions_api.get_versions_api_v1_versions_get()
        _print_versions_table(versions_info)
    except UnexpectedResponse as e:
        handle_api_error(e, "get versions")
    finally:
        client.close()


def _print_versions_table(versions_data: dict) -> None:
    """Print versions in a formatted table"""
    click.echo("Application Versions")
    click.echo("=" * 30)
    click.echo("")

    # Add CLI version and SHA first
    cli_version = get_cli_version()
    cli_sha = _get_cli_sha()

    click.echo(f"CLI Version: {cli_version}")
    click.echo(f"CLI SHA: {cli_sha}")

    # Add server versions
    for key, value in versions_data.items():
        click.echo(f"{key}: {value}")
