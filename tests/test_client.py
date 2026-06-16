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
"""Unit tests for th_cli/client.py."""

from unittest.mock import MagicMock, patch

import pytest

from th_cli.exceptions import ConfigurationError


# ---------------------------------------------------------------------------
# get_client()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetClient:
    def test_returns_api_client_instance(self):
        from th_cli.client import get_client
        from th_cli.api_lib_autogen.api_client import ApiClient

        with patch("th_cli.client.ApiClient") as mock_cls:
            mock_instance = MagicMock(spec=ApiClient)
            mock_cls.return_value = mock_instance
            result = get_client()

        assert result is mock_instance

    def test_passes_correct_host_url(self):
        from th_cli.client import get_client

        with patch("th_cli.client.ApiClient") as mock_cls:
            with patch("th_cli.client.config") as mock_config:
                mock_config.hostname = "myserver"
                mock_cls.return_value = MagicMock()
                get_client()

        call_kwargs = mock_cls.call_args
        host_value = call_kwargs[1].get("host") or call_kwargs[0][0]
        assert "myserver" in host_value

    def test_raises_configuration_error_on_exception(self):
        from th_cli.client import get_client

        with patch("th_cli.client.ApiClient", side_effect=Exception("connection refused")):
            with pytest.raises(ConfigurationError):
                get_client()

    def test_configuration_error_message_mentions_hostname(self):
        from th_cli.client import get_client

        with patch("th_cli.client.ApiClient", side_effect=Exception("boom")):
            with patch("th_cli.client.config") as mock_config:
                mock_config.hostname = "badhost"
                with pytest.raises(ConfigurationError) as exc_info:
                    get_client()
        assert "badhost" in exc_info.value.format_message()

    def test_host_url_has_http_scheme(self):
        from th_cli.client import get_client

        captured_host = []

        def capture(**kwargs):
            captured_host.append(kwargs.get("host", ""))
            return MagicMock()

        with patch("th_cli.client.ApiClient", side_effect=capture):
            with patch("th_cli.client.config") as mock_config:
                mock_config.hostname = "somehost"
                get_client()

        assert captured_host[0].startswith("http://")


# ---------------------------------------------------------------------------
# Module-level client fallback
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModuleLevelClient:
    def test_client_is_none_or_api_client(self):
        """The module-level client should be either an ApiClient instance or None."""
        import th_cli.client as client_mod
        from th_cli.api_lib_autogen.api_client import ApiClient

        assert client_mod.client is None or isinstance(client_mod.client, ApiClient)
