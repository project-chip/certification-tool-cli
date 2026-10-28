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


class _TestRunConfigsApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_read_test_run_configs_api_v1_test_run_configs__get(
        self, skip: int | None = None, limit: int | None = None
    ) -> Coroutine[Any, Any, list[m.TestRunConfig]]:
        """
        Read Test Run Configs
        """
        query_params = {}
        if skip is not None:
            query_params["skip"] = str(skip)
        if limit is not None:
            query_params["limit"] = str(limit)

        return self.api_client.request(
            type_=list[m.TestRunConfig], method="GET", url="/api/v1/test_run_configs/", params=query_params
        )

    def _build_for_create_test_run_config_api_v1_test_run_configs__post(
        self, body: m.TestRunConfigCreate
    ) -> Coroutine[Any, Any, m.TestRunConfig]:
        """
        Create Test Run Config
        """
        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(
            type_=m.TestRunConfig, method="POST", url="/api/v1/test_run_configs/", json=json_body
        )

    def _build_for_read_test_run_config_api_v1_test_run_configs__id__get(
        self, id: int
    ) -> Coroutine[Any, Any, m.TestRunConfig]:
        """
        Read Test Run Config
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunConfig, method="GET", url="/api/v1/test_run_configs/{id}", path_params=path_params
        )

    def _build_for_update_test_run_config_api_v1_test_run_configs__id__put(
        self, body: m.TestRunConfigUpdate, id: int
    ) -> Coroutine[Any, Any, m.TestRunConfig]:
        """
        Update Test Run Config
        """
        path_params = {"id": str(id)}

        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(
            type_=m.TestRunConfig,
            method="PUT",
            url="/api/v1/test_run_configs/{id}",
            path_params=path_params,
            json=json_body,
        )


class AsyncTestRunConfigsApi(_TestRunConfigsApi):
    async def read_test_run_configs_api_v1_test_run_configs__get(
        self, skip: int | None = None, limit: int | None = None
    ) -> list[m.TestRunConfig]:
        """
        Read Test Run Configs
        """
        return await self._build_for_read_test_run_configs_api_v1_test_run_configs__get(skip=skip, limit=limit)

    async def create_test_run_config_api_v1_test_run_configs__post(
        self, body: m.TestRunConfigCreate
    ) -> m.TestRunConfig:
        """
        Create Test Run Config
        """
        return await self._build_for_create_test_run_config_api_v1_test_run_configs__post(body=body)

    async def read_test_run_config_api_v1_test_run_configs__id__get(self, id: int) -> m.TestRunConfig:
        """
        Read Test Run Config
        """
        return await self._build_for_read_test_run_config_api_v1_test_run_configs__id__get(id=id)

    async def update_test_run_config_api_v1_test_run_configs__id__put(
        self, body: m.TestRunConfigUpdate, id: int
    ) -> m.TestRunConfig:
        """
        Update Test Run Config
        """
        return await self._build_for_update_test_run_config_api_v1_test_run_configs__id__put(body=body, id=id)


class SyncTestRunConfigsApi(_TestRunConfigsApi):
    def read_test_run_configs_api_v1_test_run_configs__get(
        self, skip: int | None = None, limit: int | None = None
    ) -> list[m.TestRunConfig]:
        """
        Read Test Run Configs
        """
        coroutine = self._build_for_read_test_run_configs_api_v1_test_run_configs__get(skip=skip, limit=limit)
        return get_event_loop().run_until_complete(coroutine)

    def create_test_run_config_api_v1_test_run_configs__post(self, body: m.TestRunConfigCreate) -> m.TestRunConfig:
        """
        Create Test Run Config
        """
        coroutine = self._build_for_create_test_run_config_api_v1_test_run_configs__post(body=body)
        return get_event_loop().run_until_complete(coroutine)

    def read_test_run_config_api_v1_test_run_configs__id__get(self, id: int) -> m.TestRunConfig:
        """
        Read Test Run Config
        """
        coroutine = self._build_for_read_test_run_config_api_v1_test_run_configs__id__get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def update_test_run_config_api_v1_test_run_configs__id__put(
        self, body: m.TestRunConfigUpdate, id: int
    ) -> m.TestRunConfig:
        """
        Update Test Run Config
        """
        coroutine = self._build_for_update_test_run_config_api_v1_test_run_configs__id__put(body=body, id=id)
        return get_event_loop().run_until_complete(coroutine)
