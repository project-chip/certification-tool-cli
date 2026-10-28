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
# flake8: noqa E501
from asyncio import get_event_loop
from typing import IO, TYPE_CHECKING, Any, Coroutine

from th_cli.api_lib_autogen import models as m

if TYPE_CHECKING:
    from th_cli.api_lib_autogen.api_client import ApiClient


class _DevicesApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_get_device_configs_api_v1_devices__get(self) -> Coroutine[Any, Any, dict[str, Any]]:
        """
        Get Device Configs
        """
        return self.api_client.request(type_=dict[str, Any], method="GET", url="/api/v1/devices/")

    def _build_for_add_device_config_api_v1_devices__put(
        self, body: dict[str, Any]
    ) -> Coroutine[Any, Any, dict[str, Any]]:
        """
        Add Device Config
        """
        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(type_=dict[str, Any], method="PUT", url="/api/v1/devices/", json=json_body)


class AsyncDevicesApi(_DevicesApi):
    async def get_device_configs_api_v1_devices__get(self) -> dict[str, Any]:
        """
        Get Device Configs
        """
        return await self._build_for_get_device_configs_api_v1_devices__get()

    async def add_device_config_api_v1_devices__put(self, body: dict[str, Any]) -> dict[str, Any]:
        """
        Add Device Config
        """
        return await self._build_for_add_device_config_api_v1_devices__put(body=body)


class SyncDevicesApi(_DevicesApi):
    def get_device_configs_api_v1_devices__get(self) -> dict[str, Any]:
        """
        Get Device Configs
        """
        coroutine = self._build_for_get_device_configs_api_v1_devices__get()
        return get_event_loop().run_until_complete(coroutine)

    def add_device_config_api_v1_devices__put(self, body: dict[str, Any]) -> dict[str, Any]:
        """
        Add Device Config
        """
        coroutine = self._build_for_add_device_config_api_v1_devices__put(body=body)
        return get_event_loop().run_until_complete(coroutine)
