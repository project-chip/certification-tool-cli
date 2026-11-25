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
"""Redaction of sensitive values from diagnostic output.

`th-cli doctor` output is meant to be pasted into issues and chats, so secrets
(Wi-Fi passwords, Thread network keys, DUT setup codes) and network identifiers
(IPs, MACs) are masked by default.
"""

import re
from typing import Any

REDACTED = "[redacted]"

# Matched as substrings of the key with separators removed ("network_key" -> "networkkey").
_SENSITIVE_SUBSTRINGS = (
    "password",
    "passphrase",
    "networkkey",
    "dataset",
    "token",
    "secret",
    "setupcode",
    "setuppin",
    "manualcode",
)
# Too short to match as substrings ("qr" is inside "query"); matched as whole words only.
_SENSITIVE_WORDS = {"psk", "pskc", "qr", "pin", "passcode"}

_KEY_WORD_PATTERN = (
    r"password|passphrase|network[_-]?key|(?:[a-z_]*_)?dataset(?:_hex)?|psk|pskc|token|secret|"
    r"setup[_-]?(?:code|pin)|qr(?:[_-]?code)?|manual[_-]?code|passcode"
)
_KEY_VALUE_RE = re.compile(
    rf"""(["']?(?:{_KEY_WORD_PATTERN})["']?\s*[=:]\s*)("[^"]*"|'[^']*'|[^\s,;}}]+)""",
    re.IGNORECASE,
)
_URL_USERINFO_RE = re.compile(r"([a-z][a-z0-9+.-]*://)[^/@\s]+@", re.IGNORECASE)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Full form, or compressed form (contains "::"). Plain "12:34:56" timestamps are left alone.
_IPV6_RE = re.compile(
    r"\b(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}\b|(?<![\w:])(?=[0-9a-f:]*::)[0-9a-f:]{3,39}(?![\w:])",
    re.IGNORECASE,
)
_MAC_RE = re.compile(r"\b[0-9a-f]{2}(?:[:-][0-9a-f]{2}){5}\b", re.IGNORECASE)

_LOOPBACK = {"127.0.0.1", "0.0.0.0"}


def is_sensitive_key(key: str) -> bool:
    """True if a field with this name is expected to hold a secret."""
    lowered = key.lower()
    if _SENSITIVE_WORDS & set(re.split(r"[^a-z0-9]+", lowered)):
        return True
    squashed = re.sub(r"[^a-z0-9]", "", lowered)
    return any(word in squashed for word in _SENSITIVE_SUBSTRINGS)


def redact_text(text: str, mask_network: bool = True) -> str:
    """Mask secrets, URL credentials and (optionally) IP/MAC addresses in free text."""
    text = _URL_USERINFO_RE.sub(r"\1", text)
    text = _KEY_VALUE_RE.sub(lambda m: f"{m.group(1)}{REDACTED}", text)
    if mask_network:
        text = _MAC_RE.sub("[mac]", text)
        text = _IPV6_RE.sub("[ip]", text)
        text = _IPV4_RE.sub(lambda m: m.group(0) if m.group(0) in _LOOPBACK else "[ip]", text)
    return text


def redact_data(data: Any, mask_network: bool = True) -> Any:
    """Recursively redact a JSON-like structure: by key name, then by text content."""
    if isinstance(data, dict):
        return {
            key: REDACTED if is_sensitive_key(str(key)) else redact_data(value, mask_network)
            for key, value in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [redact_data(item, mask_network) for item in data]
    if isinstance(data, str):
        return redact_text(data, mask_network)
    return data
