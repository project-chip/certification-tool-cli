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
import re
import textwrap
from collections import defaultdict
from typing import Any, Dict, List, Optional

import click
import yaml

from th_cli.api_lib_autogen.api_client import SyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.client import get_client
from th_cli.colorize import colorize_cmd_help, colorize_help
from th_cli.exceptions import CLIError, handle_api_error
from th_cli.utils import __json_string

# Constants
COLUMN_WIDTH = 23  # Fixed width for test ID columns with proper spacing


def _format_test_ids_line(test_ids: List[str]) -> str:
    """Format a list of test IDs into a padded, columnar line with 4 elements per line."""
    line_parts = []

    for j, test_id in enumerate(test_ids):
        if j < len(test_ids) - 1:  # Not the last element in the line
            # Pad to COLUMN_WIDTH for uniform spacing
            if len(test_id) > COLUMN_WIDTH:
                # If the ID is too long, truncate
                padded = test_id[:COLUMN_WIDTH]
            else:
                padded = test_id.ljust(COLUMN_WIDTH)
            line_parts.append(padded)
        else:
            # Last element doesn't need padding
            line_parts.append(test_id)

    # Join with minimal spacing
    return "  ".join(line_parts)


@click.command(
    short_help=colorize_help("List all available test cases"),
    help=colorize_cmd_help("available_tests", "Get a list of the available test cases"),
)
@click.option(
    "--json",
    is_flag=True,
    default=False,
    help=colorize_help("Print JSON response for more details"),
)
@click.option(
    "--compact",
    is_flag=True,
    default=False,
    help=colorize_help("Show test IDs only, 4 per line"),
)
@click.option(
    "--cluster",
    type=str,
    required=False,
    help=colorize_help("Filter by cluster name (e.g., ACE, CADMIN, CC)"),
)
@click.option(
    "--group-by-cluster",
    is_flag=True,
    default=False,
    help=colorize_help("Group test cases by cluster, 4 per line"),
)
def available_tests(
    json: bool = False, compact: bool = False, cluster: Optional[str] = None, group_by_cluster: bool = False
) -> None:
    """Get a list of the available test cases"""
    client = None
    try:
        client = get_client()
        sync_apis: SyncApis = SyncApis(client)
        test_collections = sync_apis.test_collections_api.read_test_collections_api_v1_test_collections__get()

        if test_collections is None:
            raise CLIError("Server did not return test_collection")

        # Check if any custom formatting options are used
        has_custom_formatting = compact or cluster or group_by_cluster

        if has_custom_formatting:
            test_cases = _extract_test_cases(test_collections)

            # Filter by cluster if specified
            if cluster:
                test_cases = _filter_by_cluster(test_cases, cluster)

            # Generate content based on formatting option
            if group_by_cluster:
                content_lines = _generate_grouped_by_cluster(test_cases)
            elif compact:
                content_lines = _generate_compact(test_cases)
            elif cluster:
                # When filtering by cluster, show detailed information
                content_lines = _generate_detailed_cluster_info(test_cases, cluster)

            # Display with Click's echo_via_pager
            content = "\n".join(content_lines)
            click.echo_via_pager(content)
        else:
            # Original behavior - full output (YAML or JSON) with pagination
            if json:
                content = __json_string(test_collections)
            else:
                yaml_dump = yaml.dump(yaml.load(__json_string(test_collections), Loader=yaml.FullLoader))
                # Don't use colorize_dump since echo_via_pager strips colors anyway
                content = yaml_dump

            # Display with Click's echo_via_pager for pagination
            click.echo_via_pager(content)
    except CLIError:
        raise  # Re-raise CLI Errors as-is
    except UnexpectedResponse as e:
        handle_api_error(e, "get available tests")
    except Exception as e:
        raise CLIError(
            f"Could not fetch the available tests: {e}. Please check if the API server is running and accessible."
        )
    finally:
        if client:
            client.close()


def _generate_compact(test_cases: List[Dict[str, str]]) -> List[str]:
    """Generate test cases in compact format with only IDs, 4 per line with compact spacing."""
    if not test_cases:
        return []

    lines = []

    # Extract only the IDs
    test_ids = [test_case["id"] for test_case in test_cases]

    # Process in batches of 4
    for i in range(0, len(test_ids), 4):
        batch = test_ids[i : i + 4]
        lines.append(_format_test_ids_line(batch))

    return lines


def _generate_grouped_by_cluster(test_cases: List[Dict[str, str]]) -> List[str]:
    """Generate test cases grouped by cluster, 4 per line with only IDs and compact spacing."""
    lines = []

    # Group by cluster
    clusters = defaultdict(list)
    for test_case in test_cases:
        clusters[test_case["cluster"]].append(test_case)

    # Generate lines for each cluster
    for cluster_name in sorted(clusters.keys()):
        lines.append(f"\n{cluster_name}:")
        lines.append("-" * (len(cluster_name) + 1))

        # Group tests in this cluster by 4 per line with compact spacing
        cluster_tests = sorted(clusters[cluster_name], key=lambda x: x["id"])
        for i in range(0, len(cluster_tests), 4):
            batch = cluster_tests[i : i + 4]
            test_ids_batch = [test_case["id"] for test_case in batch]

            # Add indentation to the formatted line
            lines.append("  " + _format_test_ids_line(test_ids_batch))

    return lines


def _generate_detailed_cluster_info(test_cases: List[Dict[str, str]], cluster_name: str) -> List[str]:
    """Generate detailed information for tests in a specific cluster."""
    if not test_cases:
        return [f"No test cases found for cluster: {cluster_name}"]

    lines = []
    lines.append(f"Test Cases for Cluster: {cluster_name.upper()}")
    lines.append("=" * (len(f"Test Cases for Cluster: {cluster_name.upper()}")))
    lines.append("")

    for test_case in test_cases:
        lines.append(f"ID: {test_case['id']}")
        lines.append(f"Title: {test_case['title']}")
        if "description" in test_case and test_case["description"]:
            description = test_case["description"]
            description_lines = textwrap.wrap(
                description,
                width=80,
                initial_indent="Description: ",
                subsequent_indent="             ",
            )
            lines.extend(description_lines)
        lines.append(f"Collection: {test_case['collection']}")
        lines.append(f"Suite: {test_case['suite']}")
        lines.append("-" * 60)
        lines.append("")

    lines.append(f"Total test cases found: {len(test_cases)}")
    return lines


def _extract_test_cases(test_collections: Any) -> List[Dict[str, str]]:
    test_cases = []

    # Navigate through the nested structure
    for collection_name, collection in test_collections.test_collections.items():
        for suite_name, suite in collection.test_suites.items():
            for test_case_id, test_case in suite.test_cases.items():
                test_info = {
                    "id": test_case.metadata.public_id,
                    "title": test_case.metadata.title,
                    "description": test_case.metadata.description if hasattr(test_case.metadata, "description") else "",
                    "collection": collection_name,
                    "suite": suite_name,
                    "cluster": _extract_cluster_from_test_id(test_case.metadata.public_id),
                }
                test_cases.append(test_info)

    return sorted(test_cases, key=lambda x: x["id"])


def _extract_cluster_from_test_id(test_id: str) -> str:
    """Extract cluster name from test ID using regex patterns."""

    # Main regex pattern to handle all common test ID formats:
    # 1. TC-CLUSTER-X.Y (e.g., TC-ACE-1.1, TC-CADMIN-1.2)
    # 2. Test_TC_CLUSTER_X_Y (e.g., Test_TC_CC_1_1)
    # 3. TC_CLUSTER_X_Y (e.g., TC_WEBRTC_1_6, TC_AUDIO_1_6)
    # 4. TC_CLUSTER-X.Y (mixed format, e.g., TC_WEBRTC-1.2)
    # 5. TC_Mixed_Case_Clusters (e.g., TC_MCORE_FS_1_1, TC_WebRTCP_2_1)

    patterns = [
        # Pattern 1: TC-CLUSTER-numbers (dash separated)
        r"^TC-([A-Z]+)-[\d.]+",
        # Pattern 2: Test_TC_CLUSTER_numbers (underscore separated with Test_ prefix)
        r"^Test_TC_([A-Z]+)_[\d_]+",
        # Pattern 3: TC_CLUSTER-numbers (mixed underscore/dash format)
        # Special handling for clusters that end with TC or TCP (like WEBRTC, WEBRTCP)
        r"^TC_([A-Z]*TCP?)-[\d.]+",  # Matches clusters ending in TC or TCP first
        r"^TC_([A-Z]+)-[\d.]+",  # Then regular clusters with dash
        # Pattern 4: TC_CLUSTER_numbers (underscore separated)
        # Handle mixed case clusters (like WebRTCP, WebRTCR, MCORE_FS)
        r"^TC_([A-Za-z_]+?)_\d+",  # Mixed case clusters with underscores
    ]

    for pattern in patterns:
        match = re.match(pattern, test_id)
        if match:
            cluster = match.group(1)
            # Convert to uppercase and replace underscores if needed
            if "_" in cluster or any(c.islower() for c in cluster):
                # For mixed case or underscore clusters, convert appropriately
                cluster = cluster.upper().replace("_", "")
            return cluster

    # Final fallback: extract any sequence of uppercase letters
    match = re.search(r"([A-Z]{2,})", test_id)
    if match:
        return match.group(1)

    return "UNKNOWN"


def _filter_by_cluster(test_cases: List[Dict[str, str]], cluster: str) -> List[Dict[str, str]]:
    """Filter test cases by cluster name (case insensitive)."""
    cluster_upper = cluster.upper()
    return [tc for tc in test_cases if tc["cluster"].upper() == cluster_upper]
