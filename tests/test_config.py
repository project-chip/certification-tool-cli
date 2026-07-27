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
"""Unit tests for th_cli/config.py."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from th_cli.config import (
    ATTRIBUTE_MAPPING,
    Config,
    LogConfig,
    PairingMode,
    VALID_PAIRING_MODES,
    find_git_root,
    get_config_search_paths,
    get_default_config,
    get_package_root,
    known_cli_path,
    load_config,
)


# ---------------------------------------------------------------------------
# known_cli_path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestKnownCliPath:
    def test_returns_path_under_home(self):
        result = known_cli_path()
        assert isinstance(result, Path)
        assert result == Path.home() / "certification-tool" / "cli"

    def test_ends_with_cli(self):
        result = known_cli_path()
        assert result.name == "cli"


# ---------------------------------------------------------------------------
# get_package_root
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetPackageRoot:
    def test_returns_path_object(self):
        result = get_package_root()
        assert isinstance(result, Path)

    def test_is_a_directory(self):
        result = get_package_root()
        assert result.is_dir()

    def test_contains_config_module(self):
        result = get_package_root()
        assert (result / "config.py").exists()


# ---------------------------------------------------------------------------
# find_git_root
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFindGitRoot:
    def test_returns_none_or_path(self):
        result = find_git_root()
        assert result is None or isinstance(result, Path)

    def test_returns_path_with_git_dir_when_found(self):
        result = find_git_root()
        if result is not None:
            assert (result / ".git").exists()

    def test_returns_none_when_no_git_dir(self, tmp_path):
        """When neither package root nor known_cli_path have .git, return None."""
        fake_pkg = tmp_path / "pkg"
        fake_pkg.mkdir()
        fake_cli = tmp_path / "cli"
        fake_cli.mkdir()

        with patch("th_cli.config.get_package_root", return_value=fake_pkg):
            with patch("th_cli.config.known_cli_path", return_value=fake_cli):
                result = find_git_root()
        assert result is None


# ---------------------------------------------------------------------------
# get_config_search_paths
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetConfigSearchPaths:
    def test_returns_list_of_paths(self):
        result = get_config_search_paths()
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    def test_includes_cwd(self):
        import os
        result = get_config_search_paths()
        assert Path(os.getcwd()) in result

    def test_includes_package_root(self):
        result = get_config_search_paths()
        assert get_package_root() in result

    def test_has_at_least_two_entries(self):
        result = get_config_search_paths()
        assert len(result) >= 2


# ---------------------------------------------------------------------------
# LogConfig
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogConfig:
    def test_default_output_log_path(self):
        cfg = LogConfig()
        assert cfg.output_log_path == "./run_logs"

    def test_custom_output_log_path(self):
        cfg = LogConfig(output_log_path="/tmp/logs")
        assert cfg.output_log_path == "/tmp/logs"

    def test_default_format_contains_level(self):
        cfg = LogConfig()
        assert "{level" in cfg.format


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfig:
    def test_default_hostname(self):
        cfg = Config()
        assert cfg.hostname == "localhost"

    def test_custom_hostname(self):
        cfg = Config(hostname="192.168.1.100")
        assert cfg.hostname == "192.168.1.100"

    def test_default_log_config_is_logconfig_instance(self):
        cfg = Config()
        assert isinstance(cfg.log_config, LogConfig)


# ---------------------------------------------------------------------------
# get_default_config
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetDefaultConfig:
    def test_returns_dict(self):
        result = get_default_config()
        assert isinstance(result, dict)

    def test_has_hostname_key(self):
        result = get_default_config()
        assert "hostname" in result

    def test_has_log_config_key(self):
        result = get_default_config()
        assert "log_config" in result

    def test_hostname_default_is_localhost(self):
        result = get_default_config()
        assert result["hostname"] == "localhost"


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLoadConfig:
    def test_returns_config_object_from_valid_config_json(self, tmp_path):
        config_data = {"hostname": "myserver", "log_config": {"output_log_path": "/tmp/logs"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("th_cli.config.get_config_search_paths", return_value=[tmp_path]):
            result = load_config()

        assert isinstance(result, Config)
        assert result.hostname == "myserver"

    def test_falls_through_to_example_when_no_config_json(self, tmp_path):
        example_data = {"hostname": "example_host"}
        example_file = tmp_path / "config.json.example"
        example_file.write_text(json.dumps(example_data))

        with patch("th_cli.config.get_config_search_paths", return_value=[tmp_path]):
            result = load_config()

        assert isinstance(result, Config)
        assert result.hostname == "example_host"

    def test_falls_back_to_defaults_when_no_files(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("th_cli.config.get_config_search_paths", return_value=[empty_dir]):
            result = load_config()

        assert isinstance(result, Config)
        assert result.hostname == "localhost"

    def test_skips_malformed_config_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("{this is: not valid json}")

        good_dir = tmp_path / "good"
        good_dir.mkdir()
        good_config = good_dir / "config.json"
        good_config.write_text(json.dumps({"hostname": "goodserver"}))

        with patch("th_cli.config.get_config_search_paths", return_value=[tmp_path, good_dir]):
            result = load_config()

        assert isinstance(result, Config)

    def test_handles_config_json_with_comments_in_example(self, tmp_path):
        """config.json.example may have comment lines (# ...)."""
        lines = ['# This is a comment\n', '{"hostname": "commented_example"}\n']
        example_file = tmp_path / "config.json.example"
        example_file.write_text("".join(lines))

        with patch("th_cli.config.get_config_search_paths", return_value=[tmp_path]):
            result = load_config()

        assert isinstance(result, Config)
        assert result.hostname == "commented_example"


# ---------------------------------------------------------------------------
# PairingMode
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPairingMode:
    def test_ble_wifi_value(self):
        assert PairingMode.BLE_WIFI.value == "ble-wifi"

    def test_ble_thread_value(self):
        assert PairingMode.BLE_THREAD.value == "ble-thread"

    def test_nfc_thread_value(self):
        assert PairingMode.NFC_THREAD.value == "nfc-thread"

    def test_nfc_ethernet_value(self):
        assert PairingMode.NFC_ETHERNET.value == "nfc-ethernet"

    def test_onnetwork_value(self):
        assert PairingMode.ONNETWORK.value == "onnetwork"

    def test_wifipaf_wifi_value(self):
        assert PairingMode.WIFIPAF_WIFI.value == "wifipaf-wifi"

    def test_valid_pairing_modes_contains_all(self):
        for mode in PairingMode:
            assert mode.value in VALID_PAIRING_MODES


# ---------------------------------------------------------------------------
# ATTRIBUTE_MAPPING
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAttributeMapping:
    def test_ssid_maps_to_wifi(self):
        assert ATTRIBUTE_MAPPING["ssid"] == ("network", "wifi")

    def test_password_maps_to_wifi(self):
        assert ATTRIBUTE_MAPPING["password"] == ("network", "wifi")

    def test_channel_maps_to_thread_dataset(self):
        assert ATTRIBUTE_MAPPING["channel"] == ("network", "thread", "dataset")

    def test_networkkey_maps_to_thread_dataset(self):
        assert ATTRIBUTE_MAPPING["networkkey"] == ("network", "thread", "dataset")

    def test_rcp_serial_path_maps_to_thread(self):
        assert ATTRIBUTE_MAPPING["rcp_serial_path"] == ("network", "thread")

    def test_operational_dataset_hex_maps_to_thread(self):
        assert ATTRIBUTE_MAPPING["operational_dataset_hex"] == ("network", "thread")
