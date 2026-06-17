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
"""Additional tests for uncovered branches in th_cli/utils.py."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from th_cli.exceptions import CLIError
from th_cli.utils import (
    add_mapped_property,
    add_unmapped_property,
    get_cli_sha,
    get_cli_version,
    get_versions,
    load_json_config,
    merge_configs,
)


# ---------------------------------------------------------------------------
# add_mapped_property
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAddMappedProperty:
    def test_creates_nested_structure(self):
        props = {}
        add_mapped_property(props, "ssid", "MyNetwork", ("network", "wifi"))
        assert props["network"]["wifi"]["ssid"] == "MyNetwork"

    def test_deep_nested_path(self):
        props = {}
        add_mapped_property(props, "channel", "11", ("network", "thread", "dataset"))
        assert props["network"]["thread"]["dataset"]["channel"] == "11"

    def test_adds_to_existing_section(self):
        props = {"network": {"wifi": {"ssid": "existing"}}}
        add_mapped_property(props, "password", "secret", ("network", "wifi"))
        assert props["network"]["wifi"]["ssid"] == "existing"
        assert props["network"]["wifi"]["password"] == "secret"

    def test_single_level_path(self):
        props = {}
        add_mapped_property(props, "key", "val", ("section",))
        assert props["section"]["key"] == "val"

    def test_overwrites_existing_key(self):
        props = {"network": {"wifi": {"ssid": "old"}}}
        add_mapped_property(props, "ssid", "new", ("network", "wifi"))
        assert props["network"]["wifi"]["ssid"] == "new"


# ---------------------------------------------------------------------------
# add_unmapped_property
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAddUnmappedProperty:
    def test_adds_to_current_section(self):
        props = {"mysection": {}}
        add_unmapped_property(props, "key", "value", "mysection")
        assert props["mysection"]["key"] == "value"

    def test_adds_to_root_when_no_section(self):
        props = {}
        add_unmapped_property(props, "rootkey", "rootval", "")
        assert props["rootkey"] == "rootval"

    def test_adds_to_root_when_section_is_none(self):
        props = {}
        add_unmapped_property(props, "k", "v", None)
        assert props["k"] == "v"

    def test_overwrites_existing_value_in_section(self):
        props = {"sec": {"k": "old"}}
        add_unmapped_property(props, "k", "new", "sec")
        assert props["sec"]["k"] == "new"


# ---------------------------------------------------------------------------
# load_json_config — additional branches
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLoadJsonConfigAdditional:
    def test_raises_cli_error_on_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json}")
        with pytest.raises(CLIError) as exc_info:
            load_json_config(str(bad))
        assert "Invalid JSON" in exc_info.value.format_message()

    def test_raises_cli_error_when_config_value_not_dict(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"config": "string_not_dict"}))
        with pytest.raises(CLIError):
            load_json_config(str(bad))

    def test_raises_cli_error_when_root_not_dict(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(CLIError):
            load_json_config(str(bad))

    def test_raises_cli_error_on_file_not_found(self, tmp_path):
        with pytest.raises(CLIError):
            load_json_config(str(tmp_path / "nonexistent.json"))

    def test_raises_cli_error_on_os_error(self, tmp_path):
        f = tmp_path / "file.json"
        f.write_text("{}")
        with patch("builtins.open", side_effect=OSError("permission denied")):
            with pytest.raises(CLIError) as exc_info:
                load_json_config(str(f))
        assert "Failed to read" in exc_info.value.format_message()


# ---------------------------------------------------------------------------
# merge_configs — additional branch (non-dict override)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMergeConfigsAdditional:
    def test_scalar_overrides_dict(self):
        base = {"a": {"b": 1}}
        override = {"a": "scalar"}
        result = merge_configs(base, override)
        assert result["a"] == "scalar"

    def test_dict_overrides_scalar(self):
        base = {"a": "scalar"}
        override = {"a": {"b": 2}}
        result = merge_configs(base, override)
        assert result["a"] == {"b": 2}

    def test_empty_override_returns_copy_of_base(self):
        base = {"x": 1, "y": {"z": 2}}
        result = merge_configs(base, {})
        assert result == base
        assert result is not base  # deep copy

    def test_empty_base_returns_copy_of_override(self):
        override = {"a": 1}
        result = merge_configs({}, override)
        assert result == {"a": 1}

    def test_does_not_mutate_base(self):
        base = {"a": {"b": 1}}
        original = json.loads(json.dumps(base))
        merge_configs(base, {"a": {"c": 2}})
        assert base == original


# ---------------------------------------------------------------------------
# get_cli_version
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetCliVersion:
    def test_returns_string(self):
        result = get_cli_version()
        assert isinstance(result, str)

    def test_returns_unknown_when_pyproject_missing(self, tmp_path):
        with patch("th_cli.utils.get_package_root", return_value=tmp_path):
            with patch("th_cli.utils.find_git_root", return_value=None):
                result = get_cli_version()
        assert result == "unknown"

    def test_returns_version_from_pyproject(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_bytes(b'[project]\nversion = "9.9.9"\n')
        with patch("th_cli.utils.get_package_root", return_value=tmp_path):
            result = get_cli_version()
        assert result == "9.9.9"

    def test_falls_back_to_git_root_when_not_in_package_root(self, tmp_path):
        git_root = tmp_path / "gitroot"
        git_root.mkdir()
        pyproject = git_root / "pyproject.toml"
        pyproject.write_bytes(b'[project]\nversion = "1.2.3"\n')
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with patch("th_cli.utils.get_package_root", return_value=empty_dir):
            with patch("th_cli.utils.find_git_root", return_value=git_root):
                result = get_cli_version()
        assert result == "1.2.3"

    def test_returns_unknown_on_ioerror(self, tmp_path):
        with patch("th_cli.utils.get_package_root", return_value=tmp_path):
            with patch("builtins.open", side_effect=IOError("read error")):
                # Need pyproject.toml to exist so the code attempts to open it
                (tmp_path / "pyproject.toml").write_bytes(b"")
                result = get_cli_version()
        assert result == "unknown"


# ---------------------------------------------------------------------------
# get_cli_sha
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetCliSha:
    def test_returns_string(self):
        result = get_cli_sha()
        assert isinstance(result, str)

    def test_returns_unknown_when_no_git_root(self):
        with patch("th_cli.utils.find_git_root", return_value=None):
            result = get_cli_sha()
        assert result == "unknown"

    def test_returns_8char_sha_on_success(self, tmp_path):
        mock_result = MagicMock()
        mock_result.stdout = "abcdef1234567890\n"
        with patch("th_cli.utils.find_git_root", return_value=tmp_path):
            with patch("th_cli.utils.subprocess.run", return_value=mock_result):
                result = get_cli_sha()
        assert result == "abcdef12"
        assert len(result) == 8

    def test_returns_unknown_on_subprocess_error(self, tmp_path):
        with patch("th_cli.utils.find_git_root", return_value=tmp_path):
            with patch(
                "th_cli.utils.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "git"),
            ):
                result = get_cli_sha()
        assert result == "unknown"

    def test_returns_unknown_when_git_not_found(self, tmp_path):
        with patch("th_cli.utils.find_git_root", return_value=tmp_path):
            with patch("th_cli.utils.subprocess.run", side_effect=FileNotFoundError("git not found")):
                result = get_cli_sha()
        assert result == "unknown"


# ---------------------------------------------------------------------------
# get_versions
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetVersions:
    def test_returns_dict_on_success(self):
        mock_client = MagicMock()
        mock_client.close = MagicMock()
        mock_version_api = MagicMock()
        mock_versions = MagicMock()
        mock_versions.model_dump.return_value = {"backend": "1.0.0"}
        mock_version_api.get_test_harness_backend_version_api_v1_version_get.return_value = mock_versions

        with patch("th_cli.utils.get_client", return_value=mock_client):
            with patch("th_cli.utils.SyncApis") as mock_sync_apis_cls:
                mock_sync_apis = MagicMock()
                mock_sync_apis.version_api = mock_version_api
                mock_sync_apis_cls.return_value = mock_sync_apis
                result = get_versions()

        assert result == {"backend": "1.0.0"}
        mock_client.close.assert_called_once()

    def test_re_raises_cli_error(self):
        with patch("th_cli.utils.get_client", side_effect=CLIError("no server")):
            with pytest.raises(CLIError):
                get_versions()

    def test_closes_client_on_exception(self):
        mock_client = MagicMock()
        mock_client.close = MagicMock()

        with patch("th_cli.utils.get_client", return_value=mock_client):
            with patch("th_cli.utils.SyncApis", side_effect=RuntimeError("boom")):
                with pytest.raises(RuntimeError):
                    get_versions()

        mock_client.close.assert_called_once()
