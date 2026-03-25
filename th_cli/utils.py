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
import copy
import json
import os
import subprocess
from typing import Any
from xml.etree.ElementTree import ParseError, fromstring

import click
import tomli

from th_cli.api_lib_autogen.api_client import SyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.client import get_client
from th_cli.colorize import colorize_dump
from th_cli.config import find_git_root, get_package_root
from th_cli.exceptions import CLIError, handle_file_error

# Constants
DEFAULT_FILE_ENCODING = "utf-8"
DEFAULT_CLI_PROJECT_NAME = "CLI Project Execution"


def __print_json(object: Any) -> None:
    click.echo(colorize_dump(__json_string(object)))


def __json_string(object: Any) -> str:
    if object is None:
        return "None"
    if isinstance(object, list):
        return json.dumps([item.model_dump() for item in object], indent=4, default=str)
    else:
        return json.dumps(object.model_dump(), indent=4, default=str)


def build_test_selection(test_collections, tests_list) -> dict:
    """Build the test selection JSON structure from test_collections and tests_list.

    Args:
        test_collections: Object containing test collections data
        tests_list: List of test IDs to select

    Returns:
        dict: Dictionary containing selected tests organized by collection and suite

    Example:
        tests_list = ["TC-ACE-1.1", "TC_ACE_1_3"]
        test_collections = {
            "SDK YAML Tests": {
                "FirstChipToolSuite": {
                    "TC-ACE-1.1": 1
                },
                "SDK Python Tests": {
                    "Python Testing Suite": {
                    "TC_ACE_1_3": 1
                    }
                }
            }
        }
    """
    selected_tests = {}

    # Convert test IDs to a set for faster lookup and normalize them (case-insensitive)
    tests_set = {test_id.strip().replace("-", "_").replace(".", "_").upper() for test_id in tests_list}

    # Iterate through test collections
    for collection_name, collection in test_collections.test_collections.items():
        selected_tests[collection_name] = {}

        # Iterate through test suites
        for suite_name, suite in collection.test_suites.items():
            selected_tests[collection_name][suite_name] = {}

            # Iterate through test cases
            for test_case_id, test_case in suite.test_cases.items():
                # Normalize the test case ID for comparison (case-insensitive)
                normalized_test_case_id = test_case_id.replace("-", "_").replace(".", "_").upper()
                if normalized_test_case_id in tests_set:
                    selected_tests[collection_name][suite_name][test_case_id] = 1

    # Remove empty collections and suites
    selected_tests = {
        collection: {suite: tests for suite, tests in suites.items() if tests}
        for collection, suites in selected_tests.items()
        if any(suites.values())
    }

    return selected_tests


def load_json_config(config_path: str) -> dict[str, Any]:
    """Load and parse a JSON configuration file with format detection.

    This function reads a JSON file and automatically detects the format:
    - Full project format: {"name": "...", "config": {...}} → Returns config dict
    - Config-only format: {...} → Returns entire dict

    This allows the same configuration file to be used with both:
    - `th-cli project create/update` (requires full format)
    - `th-cli run-tests --config` (accepts either format)

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        Parsed configuration dictionary. If the JSON contains a top-level
        "config" key, only that value is returned. Otherwise, the entire
        JSON object is returned.

    Raises:
        CLIError: If file cannot be read, JSON is invalid, or format is incorrect

    Examples:
        Full project format (extracts config):
        >>> # File: {"name": "My Project", "config": {"network": {...}}}
        >>> config = load_json_config("project.json")
        >>> print(config["network"])  # Just the config part

        Config-only format (uses as-is):
        >>> # File: {"network": {...}, "dut_config": {...}}
        >>> config = load_json_config("config.json")
        >>> print(config["network"])  # Entire file content
    """
    try:
        with open(config_path, "r", encoding=DEFAULT_FILE_ENCODING) as config_file:
            data = json.load(config_file)

        # Format detection: Check if this is full project format
        if isinstance(data, dict) and "config" in data:
            # Validate that "config" value is a dictionary
            if not isinstance(data["config"], dict):
                raise CLIError(
                    f"Invalid config file format in '{config_path}': "
                    f'"config" key must contain a dictionary, got {type(data["config"]).__name__}'
                )
            # Extract and return just the config section
            return data["config"]

        # Otherwise, treat entire JSON as config
        if not isinstance(data, dict):
            raise CLIError(
                f"Invalid config file format in '{config_path}': "
                f"Expected a JSON object (dictionary), got {type(data).__name__}"
            )

        return data

    except FileNotFoundError as e:
        handle_file_error(e, "config file")
    except json.JSONDecodeError as e:
        raise CLIError(f"Invalid JSON in config file '{config_path}': {e.msg} " f"(line {e.lineno}, column {e.colno})")
    except OSError as e:
        raise CLIError(f"Failed to read config file '{config_path}': {e}")


def merge_configs(base_config: dict[str, Any], override_config: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override configuration into base configuration.

    This function recursively merges two dictionaries, with values from
    override_config taking precedence over base_config. Nested dictionaries
    are merged recursively, while other values are replaced.

    This is the recommended function for merging JSON configurations and
    is simpler than merge_properties_to_config which handles type conversion
    from properties files.

    Args:
        base_config: Base configuration dictionary to merge into
        override_config: Configuration dictionary to merge from (takes precedence)

    Returns:
        New dictionary containing the merged configuration

    Example:
        >>> base = {"a": {"b": 1, "c": 2}, "d": 3}
        >>> override = {"a": {"b": 10}, "e": 4}
        >>> merge_configs(base, override)
        {"a": {"b": 10, "c": 2}, "d": 3, "e": 4}
    """
    result = copy.deepcopy(base_config)

    def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
        """Recursively merge source dictionary into target dictionary.

        Args:
            target: Target dictionary to merge into (modified in place)
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Both are dictionaries, recurse to merge nested structures
                _deep_merge(target[key], value)
            else:
                # Override with source value for non-dict or new keys
                target[key] = value

    _deep_merge(result, override_config)
    return result


def add_mapped_property(properties: dict, key: str, value: str, section_path: tuple) -> None:
    """Add a mapped property to the properties dictionary.

    Args:
        properties (dict): The properties dictionary to update
        key (str): The property key
        value (str): The property value
        section_path (tuple): The path to the section where the property should be added
    """
    current = properties

    # Create nested structure
    for section in section_path[:-1]:
        if section not in current:
            current[section] = {}
        current = current[section]

    # Add the value to the final section
    if section_path[-1] not in current:
        current[section_path[-1]] = {}
    current[section_path[-1]][key] = value


def add_unmapped_property(properties: dict, key: str, value: str, current_section: str) -> None:
    """Add an unmapped property to the properties dictionary.

    Args:
        properties (dict): The properties dictionary to update
        key (str): The property key
        value (str): The property value
        current_section (str): The current section name
    """
    if current_section:
        properties[current_section][key] = value
    else:
        properties[key] = value


def convert_nested_to_dict(obj, _seen=None):
    """Convert an object and all its nested objects to dictionaries, handling circular references."""
    if _seen is None:
        _seen = set()

    # Handle None and primitive types
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Check for circular references
    obj_id = id(obj)
    if obj_id in _seen:
        return str(obj)
    _seen.add(obj_id)

    # Convert object to dict
    if hasattr(obj, "__dict__"):
        result = {}
        for key, value in obj.__dict__.items():
            # Skip special attributes and thread-related objects
            if key.startswith("__") or isinstance(value, type):
                continue
            try:
                result[key] = convert_nested_to_dict(value, _seen)
            except (RecursionError, AttributeError):
                result[key] = str(value)
        return result

    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        return [convert_nested_to_dict(item, _seen) for item in obj]

    # Handle dictionaries
    if isinstance(obj, dict):
        return {k: convert_nested_to_dict(v, _seen) for k, v in obj.items()}

    # Fallback for other types
    return str(obj)


def parse_pics_xml(xml_content: str) -> dict:
    """Parse a PICS XML file and convert it to the required JSON format.

    Args:
        xml_content (str): The XML content as a string

    Returns:
        dict: Dictionary containing the PICS configuration in the required format
    """

    try:
        root = fromstring(xml_content)
        cluster_name_element = root.find("name")
        if cluster_name_element is None or not cluster_name_element.text:
            raise CLIError("PICS XML file is missing the <name> element for the cluster.")
        cluster_name = cluster_name_element.text

        # Initialize the result structure
        result = {"clusters": {cluster_name: {"name": cluster_name, "items": {}}}}

        # Parse ALL picsItem elements in the XML content
        for pics_item in root.iter("picsItem"):
            item_number_element = pics_item.find("itemNumber")
            support_element = pics_item.find("support")

            if item_number_element is not None and item_number_element.text:
                item_number = item_number_element.text

                # Handle support element - default to false if missing or empty
                support = False
                if support_element is not None and support_element.text:
                    support = support_element.text.lower() == "true"

                result["clusters"][cluster_name]["items"][item_number] = {"number": item_number, "enabled": support}

        return result

    except ParseError as e:
        raise CLIError(f"Failed to parse XML: {str(e)}")
    except Exception as e:
        raise CLIError(f"Failed processing PICS XML: {str(e)}")


def read_pics_config(pics_config_folder: str) -> dict:
    """Read PICS configuration from XML files in the specified folder.

    Args:
        pics_config_folder (str): Path to the folder containing PICS XML files

    Returns:
        dict: Dictionary containing the PICS configuration

    Raises:
        Exit: If there are any errors reading or parsing the PICS configuration
    """
    pics = {"clusters": {}}
    if not pics_config_folder:
        return pics

    try:
        # Resolve the path to handle relative paths correctly
        pics_config_folder = os.path.abspath(pics_config_folder)
        if os.path.isdir(pics_config_folder):
            # Read all XML files from the directory
            for filename in os.listdir(pics_config_folder):
                if filename.endswith(".xml"):
                    file_path = os.path.join(pics_config_folder, filename)
                    try:
                        with open(file_path, "r") as f:
                            xml_content = f.read()
                            cluster_pics = parse_pics_xml(xml_content)
                            # Merge the cluster PICS into the global structure
                            pics["clusters"].update(cluster_pics["clusters"])
                    except Exception as e:
                        raise CLIError(f"Failed to parse PICS XML file {filename}: {e}")
        else:
            raise CLIError(f"{pics_config_folder} is not a directory")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise CLIError(f"Failed to read PICS configuration: {e}")

    return pics


def get_cli_version() -> str:
    """Get CLI version from pyproject.toml"""
    try:
        # Try package root first
        package_root = get_package_root()
        pyproject_path = package_root / "pyproject.toml"

        if not pyproject_path.exists():
            # If not found in package root, try git root
            git_root = find_git_root()
            if git_root:
                pyproject_path = git_root / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomli.load(f)
                version = pyproject_data.get("project", {}).get("version")
                if version:
                    return version
        return "unknown"
    except (FileNotFoundError, IOError):
        return "unknown"


def get_cli_sha() -> str:
    """Get current CLI SHA from git"""
    try:
        # Always use git root for git operations - this ensures we find the original repo
        git_root = find_git_root()
        if not git_root:
            return "unknown"

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=git_root,
        )
        return result.stdout.strip()[:8]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_versions() -> dict:
    """Get server version information"""
    client = None
    try:
        client = get_client()
        sync_apis = SyncApis(client)
        version_api = sync_apis.version_api
        versions_info = version_api.get_test_harness_backend_version_api_v1_version_get()
        return versions_info
    except CLIError:
        raise  # Re-raise CLI Errors as-is
    except UnexpectedResponse:
        raise
    finally:
        if client:
            client.close()
