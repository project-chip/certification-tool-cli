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
"""Tests for the diagnostic output redaction helpers."""

import pytest

from th_cli.th_utils.redaction import REDACTED, is_sensitive_key, redact_data, redact_text


@pytest.mark.unit
class TestIsSensitiveKey:
    @pytest.mark.parametrize(
        "key",
        [
            "password",
            "wifi_password",
            "Passphrase",
            "network_key",
            "networkKey",
            "operational_dataset_hex",
            "psk",
            "pskc",
            "auth_token",
            "client-secret",
            "setup_code",
            "qr",
            "qr_code",
            "manual_code",
        ],
    )
    def test_sensitive(self, key: str) -> None:
        assert is_sensitive_key(key)

    @pytest.mark.parametrize("key", ["hostname", "query", "version", "ssid", "state", "sdk_docker_tag"])
    def test_not_sensitive(self, key: str) -> None:
        assert not is_sensitive_key(key)


@pytest.mark.unit
class TestRedactText:
    def test_masks_key_value_pairs(self) -> None:
        out = redact_text('ssid=home password=hunter2 "network_key": "00112233"')
        assert "hunter2" not in out
        assert "00112233" not in out
        assert "ssid=home" in out

    @pytest.mark.parametrize(
        "text", ["pin=20202021", "setup_pin: 20202021", '{"pin": "20202021"}', "wifi_pin=20202021"]
    )
    def test_masks_pin_values(self, text: str) -> None:
        assert "20202021" not in redact_text(text)
        assert "20202021" not in redact_text(text, mask_network=False)

    def test_does_not_mask_words_merely_containing_pin(self) -> None:
        assert redact_text("spinning=fast") == "spinning=fast"

    def test_masks_whole_value_with_escaped_quotes(self) -> None:
        out = redact_text(r'{"password": "ab\"secret-suffix", "ssid": "home"}')
        assert "secret-suffix" not in out
        assert '"ssid": "home"' in out

    def test_strips_url_userinfo(self) -> None:
        assert redact_text("https://user:tok@github.com/o/r.git") == "https://github.com/o/r.git"

    def test_masks_ips_and_macs(self) -> None:
        out = redact_text("host 192.168.1.20 mac aa:bb:cc:dd:ee:ff v6 fe80::1:2:3:4")
        assert "192.168.1.20" not in out
        assert "aa:bb:cc:dd:ee:ff" not in out
        assert "fe80" not in out

    def test_keeps_timestamps_and_scoped_names(self) -> None:
        assert redact_text("at 12:34:56 in std::string") == "at 12:34:56 in std::string"

    def test_masks_full_and_loopback_ipv6_forms(self) -> None:
        assert redact_text("a 2001:db8:0:0:0:0:0:1 b ::1 c fd00::1") == "a [ip] b [ip] c [ip]"

    def test_keeps_loopback(self) -> None:
        assert redact_text("localhost 127.0.0.1") == "localhost 127.0.0.1"

    def test_network_masking_can_be_disabled_but_secrets_stay_masked(self) -> None:
        out = redact_text("192.168.1.20 password=x", mask_network=False)
        assert "192.168.1.20" in out
        assert "password=x" not in out


@pytest.mark.unit
class TestRedactData:
    def test_masks_by_key_recursively(self) -> None:
        data = {"a": {"wifi": {"ssid": "home", "password": "pw"}}, "list": [{"token": "t"}, "ok"]}
        assert redact_data(data) == {
            "a": {"wifi": {"ssid": "home", "password": REDACTED}},
            "list": [{"token": REDACTED}, "ok"],
        }

    def test_masks_ips_in_string_values(self) -> None:
        assert redact_data({"host": "10.0.0.5"}) == {"host": "[ip]"}
        assert redact_data({"host": "10.0.0.5"}, mask_network=False) == {"host": "10.0.0.5"}

    def test_non_strings_pass_through(self) -> None:
        assert redact_data({"n": 3, "b": True, "x": None}) == {"n": 3, "b": True, "x": None}
