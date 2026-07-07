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


class _OperatorsApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_read_operators_api_v1_operators__get(
        self, skip: int | None = None, limit: int | None = None
    ) -> Coroutine[Any, Any, list[m.Operator]]:
        """
        Read Operators
        """
        query_params = {}
        if skip is not None:
            query_params["skip"] = str(skip)
        if limit is not None:
            query_params["limit"] = str(limit)

        return self.api_client.request(
            type_=list[m.Operator], method="GET", url="/api/v1/operators/", params=query_params
        )

    def _build_for_create_operator_api_v1_operators__post(
        self, body: m.OperatorCreate
    ) -> Coroutine[Any, Any, m.Operator]:
        """
        Create Operator
        """
        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(type_=m.Operator, method="POST", url="/api/v1/operators/", json=json_body)

    def _build_for_read_operator_api_v1_operators__id__get(self, id: int) -> Coroutine[Any, Any, m.Operator]:
        """
        Read Operator
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Operator, method="GET", url="/api/v1/operators/{id}", path_params=path_params
        )

    def _build_for_update_operator_api_v1_operators__id__put(
        self, body: m.OperatorUpdate, id: int
    ) -> Coroutine[Any, Any, m.Operator]:
        """
        Update Operator
        """
        path_params = {"id": str(id)}

        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(
            type_=m.Operator, method="PUT", url="/api/v1/operators/{id}", path_params=path_params, json=json_body
        )

    def _build_for_delete_operator_api_v1_operators__id__delete(self, id: int) -> Coroutine[Any, Any, m.Operator]:
        """
        Delete Operator
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Operator, method="DELETE", url="/api/v1/operators/{id}", path_params=path_params
        )


class AsyncOperatorsApi(_OperatorsApi):
    async def read_operators_api_v1_operators__get(
        self, skip: int | None = None, limit: int | None = None
    ) -> list[m.Operator]:
        """
        Read Operators
        """
        return await self._build_for_read_operators_api_v1_operators__get(skip=skip, limit=limit)

    async def create_operator_api_v1_operators__post(self, body: m.OperatorCreate) -> m.Operator:
        """
        Create Operator
        """
        return await self._build_for_create_operator_api_v1_operators__post(body=body)

    async def read_operator_api_v1_operators__id__get(self, id: int) -> m.Operator:
        """
        Read Operator
        """
        return await self._build_for_read_operator_api_v1_operators__id__get(id=id)

    async def update_operator_api_v1_operators__id__put(self, body: m.OperatorUpdate, id: int) -> m.Operator:
        """
        Update Operator
        """
        return await self._build_for_update_operator_api_v1_operators__id__put(body=body, id=id)

    async def delete_operator_api_v1_operators__id__delete(self, id: int) -> m.Operator:
        """
        Delete Operator
        """
        return await self._build_for_delete_operator_api_v1_operators__id__delete(id=id)


class SyncOperatorsApi(_OperatorsApi):
    def read_operators_api_v1_operators__get(
        self, skip: int | None = None, limit: int | None = None
    ) -> list[m.Operator]:
        """
        Read Operators
        """
        coroutine = self._build_for_read_operators_api_v1_operators__get(skip=skip, limit=limit)
        return get_event_loop().run_until_complete(coroutine)

    def create_operator_api_v1_operators__post(self, body: m.OperatorCreate) -> m.Operator:
        """
        Create Operator
        """
        coroutine = self._build_for_create_operator_api_v1_operators__post(body=body)
        return get_event_loop().run_until_complete(coroutine)

    def read_operator_api_v1_operators__id__get(self, id: int) -> m.Operator:
        """
        Read Operator
        """
        coroutine = self._build_for_read_operator_api_v1_operators__id__get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def update_operator_api_v1_operators__id__put(self, body: m.OperatorUpdate, id: int) -> m.Operator:
        """
        Update Operator
        """
        coroutine = self._build_for_update_operator_api_v1_operators__id__put(body=body, id=id)
        return get_event_loop().run_until_complete(coroutine)

    def delete_operator_api_v1_operators__id__delete(self, id: int) -> m.Operator:
        """
        Delete Operator
        """
        coroutine = self._build_for_delete_operator_api_v1_operators__id__delete(id=id)
        return get_event_loop().run_until_complete(coroutine)
