#
# Copyright (c) 2023 Project CHIP Authors
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
from typing import Any

import click
import yaml
from click.exceptions import Exit

from app.api_lib_autogen.api_client import SyncApis
from app.client import get_client
from app.exceptions import CLIError
from app.utils import __json_string, __print_json

@click.command()
@click.option(
    "--json",
    is_flag=True,
    flag_value=True,
    help="Print JSON response for more details",
)
def available_tests(json: bool = False) -> None:
    """Get a list of available tests"""
    try:
        client = get_client()
        sync_apis: SyncApis = SyncApis(client)
        test_collections = sync_apis.test_collections_api.read_test_collections_api_v1_test_collections_get()

        if test_collections is None:
            raise CLIError("Server did not return test_collection")

        if json:
            __print_json(test_collections)
        else:
            __print_yaml(test_collections)
    except Exception as e:
        raise CLIError(f"Could not fetch the available tests: {e}. Please check if the API server is running and accessible.")
    finally:
        sync_apis.client.close()


def __print_yaml(object: Any) -> None:
    click.echo(yaml.dump(yaml.load(__json_string(object), Loader=yaml.FullLoader)))
