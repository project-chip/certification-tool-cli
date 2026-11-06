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

import click
from httpx import Timeout, TimeoutException

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.api_client import SyncApis
from th_cli.api_lib_autogen.exceptions import ResponseHandlingException, UnexpectedResponse
from th_cli.client import get_client
from th_cli.colorize import colorize_cmd_help, colorize_help, colorize_success, colorize_warning
from th_cli.exceptions import CLIError, handle_api_error

# Rescanning regenerates the Python test JSON files via the SDK container,
# which can take significantly longer than httpx's 5s default read timeout.
RESCAN_TIMEOUT = Timeout(120.0, connect=10.0)  # 120s total, 10s connect


def _render_changes(changes: api_models.RescanChanges) -> list[str]:
    """Render the test case changes grouped by collection, followed by the collections
    that did not change."""
    markers = (("+", "added", changes.added), ("~", "modified", changes.modified), ("-", "removed", changes.removed))

    lines_by_collection: dict[str, list[str]] = {}
    for marker, label, test_cases in markers:
        for change in test_cases:
            lines_by_collection.setdefault(change.collection, []).append(f"  {marker} {change.test_case:<30} {label}")

    lines: list[str] = []
    for collection, collection_lines in lines_by_collection.items():
        lines.append("")
        lines.append(collection)
        lines.extend(collection_lines)

    unchanged = [name for name in changes.collections if name not in lines_by_collection]
    if unchanged:
        lines.append(f"No changes in: {', '.join(unchanged)}")
    return lines


def _render_errors(errors: list[api_models.ScriptError]) -> list[str]:
    lines = ["", "Scripts that could not be parsed (skipped):"]
    for error in errors:
        reason = " ".join(error.reason.split())
        lines.append(f"  ! {error.script}: {reason}" if error.script else f"  ! {reason}")
    return lines


def _render_overrides(overrides: api_models.CustomOverrides) -> list[str]:
    lines: list[str] = []
    if overrides.overriding:
        lines.append("")
        lines.append("Custom files overriding SDK modules (used by every test that imports them):")
        lines.extend(f"  ! {name}" for name in overrides.overriding)
    if overrides.unused_copies:
        lines.append("")
        lines.append("Custom files with the same name as an SDK file that nothing imports (override nothing):")
        lines.extend(f"  - {name}" for name in overrides.unused_copies)
    return lines


def print_rescan_report(response: api_models.TestCollections) -> None:
    """Print the outcome of a rescan, including what it changed."""
    collection_count = len(response.test_collections)
    changes = response.changes

    summary = f"Rescanned test collections successfully ({collection_count} found)"
    if changes is None:
        # Backend that predates the change report
        click.echo(colorize_success(summary))
        return

    has_changes = bool(changes.added or changes.modified or changes.removed)
    if has_changes:
        click.echo(colorize_success(summary))
        for line in _render_changes(changes):
            click.echo(line)
    else:
        click.echo(colorize_success(f"{summary}. No changes detected."))

    if changes.errors:
        click.echo(colorize_warning("\n".join(_render_errors(changes.errors))))

    if changes.custom_overrides:
        override_lines = _render_overrides(changes.custom_overrides)
        if override_lines:
            click.echo(colorize_warning("\n".join(override_lines)))


@click.command(
    short_help=colorize_help("Rescan available test collections"),
    help=colorize_cmd_help(
        "rescan_tests",
        "Re-run test collection discovery on the backend, picking up newly "
        "added or edited side-loaded test scripts without restarting it",
    ),
)
def rescan_tests() -> None:
    """Rescan available test collections"""
    client = None
    try:
        client = get_client()
        client._async_client.timeout = RESCAN_TIMEOUT
        sync_apis: SyncApis = SyncApis(client)
        test_collections = sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post()

        if test_collections is None:
            raise CLIError("Server did not return test_collections")

        print_rescan_report(test_collections)
    except CLIError:
        raise  # Re-raise CLI Errors as-is
    except ResponseHandlingException as e:
        # Rescanning can outlast even the extended timeout above (e.g. a
        # slow SDK container pull). The backend keeps running the rescan to
        # completion regardless of whether the CLI is still waiting on it.
        if isinstance(e.error, TimeoutException):
            click.echo(colorize_success("Rescan request sent (backend may still be processing)"))
        else:
            raise CLIError(
                f"Could not rescan test collections: {e}. Please check if the API server is running and accessible."
            )
    except UnexpectedResponse as e:
        handle_api_error(e, "rescan test collections")
    except Exception as e:
        raise CLIError(
            f"Could not rescan test collections: {e}. Please check if the API server is running and accessible."
        )
    finally:
        if client:
            client.close()
