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


class _VersionApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_get_test_harness_backend_version_api_v1_version_get(
        self,
    ) -> Coroutine[Any, Any, m.TestHarnessBackendVersion]:
        """
        Get Test Harness Backend Version
        """
        return self.api_client.request(type_=m.TestHarnessBackendVersion, method="GET", url="/api/v1/version")


class AsyncVersionApi(_VersionApi):
    async def get_test_harness_backend_version_api_v1_version_get(self) -> m.TestHarnessBackendVersion:
        """
        Get Test Harness Backend Version
        """
        return await self._build_for_get_test_harness_backend_version_api_v1_version_get()


class SyncVersionApi(_VersionApi):
    def get_test_harness_backend_version_api_v1_version_get(self) -> m.TestHarnessBackendVersion:
        """
        Get Test Harness Backend Version
        """
        coroutine = self._build_for_get_test_harness_backend_version_api_v1_version_get()
        return get_event_loop().run_until_complete(coroutine)
