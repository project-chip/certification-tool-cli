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

from th_cli.api_lib_autogen.api_client import SyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.client import get_client
from th_cli.colorize import colorize_cmd_help, colorize_help, colorize_success
from th_cli.exceptions import CLIError, handle_api_error


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
        sync_apis: SyncApis = SyncApis(client)
        test_collections = sync_apis.test_collections_api.rescan_test_collections_api_v1_test_collections_rescan_post()

        if test_collections is None:
            raise CLIError("Server did not return test_collections")

        collection_count = len(test_collections.test_collections)
        click.echo(colorize_success(f"Rescanned test collections successfully ({collection_count} found)"))
    except CLIError:
        raise  # Re-raise CLI Errors as-is
    except UnexpectedResponse as e:
        handle_api_error(e, "rescan test collections")
    except Exception as e:
        raise CLIError(
            f"Could not rescan test collections: {e}. Please check if the API server is running and accessible."
        )
    finally:
        if client:
            client.close()
