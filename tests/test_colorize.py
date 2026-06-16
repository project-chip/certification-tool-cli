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
"""Unit tests for th_cli/colorize.py."""

import pytest

from th_cli.colorize import (
    ColorConfig,
    HierarchyEnum,
    TextTypeEnum,
    colorize_cmd_help,
    colorize_dump,
    colorize_error,
    colorize_header,
    colorize_help,
    colorize_hierarchy_prefix,
    colorize_key_value,
    colorize_runner_state,
    colorize_state,
    colorize_success,
    colorize_warning,
    italic,
    set_colors_enabled,
)
from th_cli.api_lib_autogen.models import TestRunnerState, TestStateEnum


# ---------------------------------------------------------------------------
# ColorConfig — construction and environment variable
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorConfigInit:
    """Tests for ColorConfig.__init__ and the TH_CLI_NO_COLOR env var."""

    def test_colors_enabled_by_default(self, monkeypatch):
        monkeypatch.delenv("TH_CLI_NO_COLOR", raising=False)
        cfg = ColorConfig()
        assert cfg.colors_enabled is True

    def test_colors_disabled_when_env_is_1(self, monkeypatch):
        monkeypatch.setenv("TH_CLI_NO_COLOR", "1")
        cfg = ColorConfig()
        assert cfg.colors_enabled is False

    def test_colors_disabled_when_env_is_true(self, monkeypatch):
        monkeypatch.setenv("TH_CLI_NO_COLOR", "true")
        cfg = ColorConfig()
        assert cfg.colors_enabled is False

    def test_colors_disabled_when_env_is_yes(self, monkeypatch):
        monkeypatch.setenv("TH_CLI_NO_COLOR", "yes")
        cfg = ColorConfig()
        assert cfg.colors_enabled is False

    def test_colors_enabled_when_env_is_0(self, monkeypatch):
        monkeypatch.setenv("TH_CLI_NO_COLOR", "0")
        cfg = ColorConfig()
        assert cfg.colors_enabled is True

    def test_colors_enabled_when_env_is_false(self, monkeypatch):
        monkeypatch.setenv("TH_CLI_NO_COLOR", "false")
        cfg = ColorConfig()
        assert cfg.colors_enabled is True

    def test_colors_enabled_property_returns_bool(self, monkeypatch):
        monkeypatch.delenv("TH_CLI_NO_COLOR", raising=False)
        cfg = ColorConfig()
        assert isinstance(cfg.colors_enabled, bool)


# ---------------------------------------------------------------------------
# ColorConfig — get_state_color
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorConfigGetStateColor:
    def test_passed_state_returns_green(self):
        cfg = ColorConfig()
        assert cfg.get_state_color(TestStateEnum.passed.value) == "green"

    def test_failed_state_returns_red(self):
        cfg = ColorConfig()
        assert cfg.get_state_color(TestStateEnum.failed.value) == "red"

    def test_error_state_returns_red(self):
        cfg = ColorConfig()
        assert cfg.get_state_color(TestStateEnum.error.value) == "red"

    def test_executing_state_returns_yellow(self):
        cfg = ColorConfig()
        assert cfg.get_state_color(TestStateEnum.executing.value) == "yellow"

    def test_unknown_state_returns_white(self):
        cfg = ColorConfig()
        assert cfg.get_state_color("nonexistent_state") == "white"

    def test_case_insensitive_lookup(self):
        cfg = ColorConfig()
        assert cfg.get_state_color("PASSED") == "green"


# ---------------------------------------------------------------------------
# ColorConfig — get_runner_state_color
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorConfigGetRunnerStateColor:
    def test_idle_state(self):
        cfg = ColorConfig()
        assert cfg.get_runner_state_color(TestRunnerState.idle.value) == "bright_black"

    def test_ready_state(self):
        cfg = ColorConfig()
        assert cfg.get_runner_state_color(TestRunnerState.ready.value) == "green"

    def test_loading_state(self):
        cfg = ColorConfig()
        assert cfg.get_runner_state_color(TestRunnerState.loading.value) == "yellow"

    def test_running_state(self):
        cfg = ColorConfig()
        assert cfg.get_runner_state_color(TestRunnerState.running.value) == "red"

    def test_unknown_runner_state_returns_white(self):
        cfg = ColorConfig()
        assert cfg.get_runner_state_color("unknown_runner") == "white"


# ---------------------------------------------------------------------------
# ColorConfig — get_text_color
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorConfigGetTextColor:
    def test_success_text(self):
        cfg = ColorConfig()
        assert cfg.get_text_color(TextTypeEnum.SUCCESS.value) == "green"

    def test_error_text(self):
        cfg = ColorConfig()
        assert cfg.get_text_color(TextTypeEnum.ERROR.value) == "red"

    def test_warning_text(self):
        cfg = ColorConfig()
        assert cfg.get_text_color(TextTypeEnum.WARNING.value) == "yellow"

    def test_unknown_text_type_returns_white(self):
        cfg = ColorConfig()
        assert cfg.get_text_color("notype") == "white"


# ---------------------------------------------------------------------------
# ColorConfig — get_hierarchy_color
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorConfigGetHierarchyColor:
    def test_test_run_hierarchy(self):
        cfg = ColorConfig()
        assert cfg.get_hierarchy_color(HierarchyEnum.TEST_RUN.value) == "blue"

    def test_test_suite_hierarchy(self):
        cfg = ColorConfig()
        assert cfg.get_hierarchy_color(HierarchyEnum.TEST_SUITE.value) == "magenta"

    def test_test_case_hierarchy(self):
        cfg = ColorConfig()
        assert cfg.get_hierarchy_color(HierarchyEnum.TEST_CASE.value) == "cyan"

    def test_test_step_hierarchy(self):
        cfg = ColorConfig()
        assert cfg.get_hierarchy_color(HierarchyEnum.TEST_STEP.value) == "bright_black"

    def test_unknown_hierarchy_returns_white(self):
        cfg = ColorConfig()
        assert cfg.get_hierarchy_color("unknown_level") == "white"


# ---------------------------------------------------------------------------
# set_colors_enabled
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSetColorsEnabled:
    def test_disable_colors(self):
        set_colors_enabled(True)   # ensure enabled first
        set_colors_enabled(False)
        from th_cli.colorize import color_config
        assert color_config.colors_enabled is False

    def test_enable_colors(self):
        set_colors_enabled(False)  # ensure disabled first
        set_colors_enabled(True)
        from th_cli.colorize import color_config
        assert color_config.colors_enabled is True


# ---------------------------------------------------------------------------
# colorize_state
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeState:
    def test_returns_uppercase_in_brackets(self):
        set_colors_enabled(False)
        result = colorize_state("passed")
        assert result == "[PASSED]"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_state("failed")
        assert "FAILED" in result
        assert len(result) > 0

    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        result = colorize_state("error")
        assert result == "[ERROR]"


# ---------------------------------------------------------------------------
# colorize_runner_state
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeRunnerState:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        result = colorize_runner_state("idle")
        assert result == "IDLE"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_runner_state("running")
        assert "RUNNING" in result


# ---------------------------------------------------------------------------
# colorize_hierarchy_prefix
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeHierarchyPrefix:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        result = colorize_hierarchy_prefix("Suite name", "test_suite")
        assert result == "Suite name"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_hierarchy_prefix("Suite name", "test_suite")
        assert "Suite name" in result


# ---------------------------------------------------------------------------
# colorize_cmd_help
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeCmdHelp:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        result = colorize_cmd_help("run", "Execute tests")
        assert result == "run: Execute tests"

    def test_contains_cmd_and_description_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_cmd_help("run", "Execute tests")
        assert "run" in result
        assert "Execute tests" in result


# ---------------------------------------------------------------------------
# colorize_help
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeHelp:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        result = colorize_help("Some help text")
        assert result == "Some help text"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_help("Some help text")
        assert "Some help text" in result


# ---------------------------------------------------------------------------
# colorize_success
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeSuccess:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        assert colorize_success("Done!") == "Done!"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_success("Done!")
        assert "Done!" in result


# ---------------------------------------------------------------------------
# colorize_error
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeError:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        assert colorize_error("Oops!") == "Oops!"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_error("Oops!")
        assert "Oops!" in result


# ---------------------------------------------------------------------------
# colorize_warning
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeWarning:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        assert colorize_warning("Watch out!") == "Watch out!"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_warning("Watch out!")
        assert "Watch out!" in result


# ---------------------------------------------------------------------------
# colorize_key_value
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeKeyValue:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        result = colorize_key_value("status", "ok")
        assert result == "status: ok"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_key_value("status", "ok")
        assert "status" in result
        assert "ok" in result

    def test_value_converted_to_string(self):
        set_colors_enabled(False)
        result = colorize_key_value("count", 42)
        assert "42" in result


# ---------------------------------------------------------------------------
# colorize_header
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeHeader:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        assert colorize_header("RESULTS") == "RESULTS"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_header("RESULTS")
        assert "RESULTS" in result


# ---------------------------------------------------------------------------
# colorize_dump
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestColorizeDump:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        assert colorize_dump('{"key": "val"}') == '{"key": "val"}'

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = colorize_dump('{"key": "val"}')
        assert "key" in result


# ---------------------------------------------------------------------------
# italic
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestItalic:
    def test_plain_when_colors_disabled(self):
        set_colors_enabled(False)
        assert italic("hello") == "hello"

    def test_non_empty_with_colors_enabled(self):
        set_colors_enabled(True)
        result = italic("hello")
        assert "hello" in result
