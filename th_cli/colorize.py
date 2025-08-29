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

import click

from th_cli.api_lib_autogen.models import TestRunnerState, TestStateEnum


class ColorConfig:
    """Configuration for test output colors."""

    # Default color mapping for different test states
    DEFAULT_STATE_COLORS: dict[str, str] = {
        TestStateEnum.PASSED.value: "green",
        TestStateEnum.FAILED.value: "red",
        TestStateEnum.ERROR.value: "red",
        TestStateEnum.CANCELLED.value: "bright_red",
        TestStateEnum.EXECUTING.value: "yellow",
        TestStateEnum.PENDING.value: "bright_white",
        TestStateEnum.PENDING_ACTUATION.value: "bright_white",
        TestStateEnum.NOT_APPLICABLE.value: "bright_black",
    }

    RUNNER_STATE_COLORS: dict[str, str] = {
        TestRunnerState.IDLE.value: "bright_black",
        TestRunnerState.READY.value: "green",
        TestRunnerState.LOADING.value: "yellow",
        TestRunnerState.RUNNING.value: "red",
    }

    # Hierarchy colors for different levels of test organization
    TEST_HIERARCHY_COLORS: dict[str, str] = {
        "test_run": "blue",
        "test_suite": "magenta",
        "test_case": "cyan",
        "test_step": "bright_black",
    }

    # Default colors for logs
    TEXT_COLORS: dict[str, str] = {
        "header": "bright_blue",
        "key": "bright_blue",
        "value": "bright_black",
        "help": "bright_black",
        "dump": "bright_black",
        "success": "green",
        "error": "red",
    }

    def __init__(self):
        # Check if colors should be disabled via environment variable
        self._colors_enabled = os.getenv("TH_CLI_NO_COLOR", "").lower() not in ("1", "true", "yes")

    @property
    def colors_enabled(self) -> bool:
        """Check if colors are enabled."""
        return self._colors_enabled

    def get_state_color(self, state: str) -> str:
        """Get color for a test state."""
        return self.DEFAULT_STATE_COLORS.get(state.lower(), "white")

    def get_runner_state_color(self, state: str) -> str:
        """Get color for a test runner state."""
        return self.RUNNER_STATE_COLORS.get(state.lower(), "white")

    def get_text_color(self, text_type: str) -> str:
        """Get color for a log type."""
        return self.TEXT_COLORS.get(text_type.lower(), "white")

    def get_hierarchy_color(self, level: str) -> str:
        """Get color for a hierarchy level."""
        return self.TEST_HIERARCHY_COLORS.get(level.lower(), "white")


# Global color configuration instance
color_config = ColorConfig()


def colorize_state(state_name: str) -> str:
    """
    Colorize test state based on semantic meaning.

    Args:
        state_name: The name of the test state (e.g., "passed", "failed")

    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    state_text = f"[{state_name.upper()}]"

    if not color_config.colors_enabled:
        return state_text

    color = color_config.get_state_color(state_name)
    return click.style(state_text, fg=color, bold=True)


def colorize_runner_state(runner_state_name: str) -> str:
    """
    Colorize test runner state based on semantic meaning.

    Args:
        runner_state_name: The name of the test runner state (e.g., "idle", "running")

    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    blink = runner_state_name.lower() == TestRunnerState.RUNNING.value
    state_text = f"{runner_state_name.upper()}"

    if not color_config.colors_enabled:
        return state_text

    color = color_config.get_runner_state_color(runner_state_name)
    return click.style(state_text, fg=color, bold=True, blink=blink)


def colorize_hierarchy_prefix(text: str, level: str) -> str:
    """
    Colorize hierarchy prefixes (e.g., test suite titles, test case titles).

    Args:
        text: The text to colorize
        level: The hierarchy level ("test_run", "test_suite", "test_case", "test_step")

    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    if not color_config.colors_enabled:
        return text

    color = color_config.get_hierarchy_color(level)
    return click.style(text, fg=color)


def colorize_help(help_message: str) -> str:
    """
    Colorize success messages in logs.

    Args:
        help_message: The help message to colorize
    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    if not color_config.colors_enabled:
        return help_message

    color = color_config.get_text_color("help")
    return click.style(help_message, fg=color)


def colorize_success(success_message: str) -> str:
    """
    Colorize success messages in logs.

    Args:
        success_message: The success message to colorize
    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    if not color_config.colors_enabled:
        return success_message

    color = color_config.get_text_color("success")
    return click.style(success_message, fg=color, bold=True)


def colorize_error(error_message: str) -> str:
    """
    Colorize error messages in logs.

    Args:
        error_message: The error message to colorize
    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    if not color_config.colors_enabled:
        return error_message

    color = color_config.get_text_color("error")
    return click.style(error_message, fg=color, bold=True, italic=True)


def colorize_key_value(key: str, value: any) -> str:
    """
    Colorize key-value pairs in logs.

    Args:
        key: The key part of the log entry
        value: The value part of the log entry
    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    value_as_str = str(value)
    if not color_config.colors_enabled:
        return f"{key}: {value}"

    colored_key = click.style(key, fg=color_config.get_text_color("key"), bold=True)
    colored_value = click.style(value_as_str, fg=color_config.get_text_color("value"))
    return f"{colored_key}: {colored_value}"


def colorize_header(header: str) -> str:
    """
    Colorize log headers.

    Args:
        header: The header text to colorize
    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    if not color_config.colors_enabled:
        return header

    color = color_config.get_text_color("header")
    return click.style(header, fg=color, bold=True, underline=True)


def colorize_dump(dump: str) -> str:
    """
    Colorize log dumps (e.g., JSON or YAML dumps).

    Args:
        dump: The dump text to colorize
    Returns:
        Colored string if colors are enabled, plain string otherwise
    """
    if not color_config.colors_enabled:
        return dump

    color = color_config.get_text_color("dump")
    return click.style(dump, fg=color, italic=True)


def italic(text: str) -> str:
    """
    Italicize text.

    Args:
        text: The text to italicize
    Returns:
        Italicized string
    """
    if not color_config.colors_enabled:
        return text

    return click.style(text, italic=True)


def set_colors_enabled(enabled: bool) -> None:
    """
    Programmatically enable or disable colors.

    Args:
        enabled: Whether to enable colors
    """
    color_config._colors_enabled = enabled
