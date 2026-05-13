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


class _TestRunExecutionsApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_read_test_run_executions_api_v1_test_run_executions__get(
        self,
        project_id: int | None = None,
        archived: bool | None = None,
        search_query: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        sort_order: str | None = None,
    ) -> Coroutine[Any, Any, list[m.TestRunExecutionWithStats]]:
        """
        Read Test Run Executions
        """
        query_params = {}
        if project_id is not None:
            query_params["project_id"] = str(project_id)
        if archived is not None:
            query_params["archived"] = str(archived)
        if search_query is not None:
            query_params["search_query"] = str(search_query)
        if skip is not None:
            query_params["skip"] = str(skip)
        if limit is not None:
            query_params["limit"] = str(limit)
        if sort_order is not None:
            query_params["sort_order"] = str(sort_order)

        return self.api_client.request(
            type_=list[m.TestRunExecutionWithStats],
            method="GET",
            url="/api/v1/test_run_executions/",
            params=query_params,
        )

    def _build_for_create_test_run_execution_api_v1_test_run_executions__post(
        self, body: m.BodyCreateTestRunExecutionApiV1TestRunExecutionsPost, certification_mode: bool | None = None
    ) -> Coroutine[Any, Any, m.TestRunExecutionWithChildren]:
        """
        Create Test Run Execution
        """
        query_params = {}
        if certification_mode is not None:
            query_params["certification_mode"] = str(certification_mode)

        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="POST",
            url="/api/v1/test_run_executions/",
            params=query_params,
            json=json_body,
        )

    def _build_for_create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
        self, body: m.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost
    ) -> Coroutine[Any, Any, m.TestRunExecutionWithChildren]:
        """
        Create Cli Test Run Execution
        """
        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren, method="POST", url="/api/v1/test_run_executions/cli", json=json_body
        )

    def _build_for_rename_test_run_execution_api_v1_test_run_executions__id__rename_put(
        self, id: int, new_execution_name: str
    ) -> Coroutine[Any, Any, m.TestRunExecutionWithChildren]:
        """
        Rename Test Run Execution
        """
        path_params = {"id": str(id)}

        query_params = {"new_execution_name": str(new_execution_name)}

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="PUT",
            url="/api/v1/test_run_executions/{id}/rename",
            path_params=path_params,
            params=query_params,
        )

    def _build_for_abort_testing_api_v1_test_run_executions_abort_testing_post(
        self,
    ) -> Coroutine[Any, Any, dict[str, str]]:
        """
        Abort Testing
        """
        return self.api_client.request(
            type_=dict[str, str], method="POST", url="/api/v1/test_run_executions/abort-testing"
        )

    def _build_for_get_test_runner_status_api_v1_test_run_executions_status_get(
        self,
    ) -> Coroutine[Any, Any, m.TestRunnerStatus]:
        """
        Get Test Runner Status
        """
        return self.api_client.request(type_=m.TestRunnerStatus, method="GET", url="/api/v1/test_run_executions/status")

    def _build_for_get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
        self,
        discriminator: str | None = None,
        setup_pin_code: str | None = None,
        version: int | None = None,
        vendor_id: int | None = None,
        product_id: int | None = None,
    ) -> Coroutine[Any, Any, m.ChipServerInfo]:
        """
        Get Chip Server Info
        """
        query_params = {}
        if discriminator is not None:
            query_params["discriminator"] = str(discriminator)
        if setup_pin_code is not None:
            query_params["setup_pin_code"] = str(setup_pin_code)
        if version is not None:
            query_params["version"] = str(version)
        if vendor_id is not None:
            query_params["vendor_id"] = str(vendor_id)
        if product_id is not None:
            query_params["product_id"] = str(product_id)

        return self.api_client.request(
            type_=m.ChipServerInfo,
            method="GET",
            url="/api/v1/test_run_executions/chip-server/info",
            params=query_params,
        )

    def _build_for_read_test_run_execution_api_v1_test_run_executions__id__get(
        self, id: int
    ) -> Coroutine[Any, Any, m.TestRunExecutionWithChildren]:
        """
        Read Test Run Execution
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="GET",
            url="/api/v1/test_run_executions/{id}",
            path_params=path_params,
        )

    def _build_for_remove_test_run_execution_api_v1_test_run_executions__id__delete(
        self, id: int
    ) -> Coroutine[Any, Any, m.TestRunExecutionInDBBase]:
        """
        Remove Test Run Execution
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecutionInDBBase,
            method="DELETE",
            url="/api/v1/test_run_executions/{id}",
            path_params=path_params,
        )

    def _build_for_start_test_run_execution_api_v1_test_run_executions__id__start_post(
        self, id: int
    ) -> Coroutine[Any, Any, m.TestRunExecutionWithChildren]:
        """
        Start Test Run Execution
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="POST",
            url="/api/v1/test_run_executions/{id}/start",
            path_params=path_params,
        )

    def _build_for_archive_api_v1_test_run_executions__id__archive_post(
        self, id: int
    ) -> Coroutine[Any, Any, m.TestRunExecution]:
        """
        Archive
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecution,
            method="POST",
            url="/api/v1/test_run_executions/{id}/archive",
            path_params=path_params,
        )

    def _build_for_unarchive_api_v1_test_run_executions__id__unarchive_post(
        self, id: int
    ) -> Coroutine[Any, Any, m.TestRunExecution]:
        """
        Unarchive
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecution,
            method="POST",
            url="/api/v1/test_run_executions/{id}/unarchive",
            path_params=path_params,
        )

    def _build_for_repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post(
        self, id: int, title: str | None = None
    ) -> Coroutine[Any, Any, m.TestRunExecutionWithChildren]:
        """
        Repeat Test Run Execution
        """
        path_params = {"id": str(id)}

        query_params = {}
        if title is not None:
            query_params["title"] = str(title)

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="POST",
            url="/api/v1/test_run_executions/{id}/repeat",
            path_params=path_params,
            params=query_params,
        )

    def _build_for_download_log_api_v1_test_run_executions__id__log_get(
        self, id: int, json_entries: bool | None = None, download: bool | None = None
    ) -> Coroutine[Any, Any, None]:
        """
        Download Log
        """
        path_params = {"id": str(id)}

        query_params = {}
        if json_entries is not None:
            query_params["json_entries"] = str(json_entries)
        if download is not None:
            query_params["download"] = str(download)

        return self.api_client.request(
            type_=None,
            method="GET",
            url="/api/v1/test_run_executions/{id}/log",
            path_params=path_params,
            params=query_params,
        )

    def _build_for_download_grouped_log_api_v1_test_run_executions__id__grouped_log_get(
        self, id: int
    ) -> Coroutine[Any, Any, bytes]:
        """
        Download Grouped Log
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=bytes, method="GET", url="/api/v1/test_run_executions/{id}/grouped-log", path_params=path_params
        )

    def _build_for_upload_file_api_v1_test_run_executions_file_upload__post(
        self, body: m.BodyUploadFileApiV1TestRunExecutionsFileUploadPost
    ) -> Coroutine[Any, Any, dict[str, Any]]:
        """
        Upload File
        """
        files: dict[str, IO[Any]] = {}
        data: dict[str, Any] = {}

        # Process body fields to populate files and data dictionaries
        if body is not None:
            # Process field: file
            if hasattr(body, "file"):
                field_value = getattr(body, "file")
                if field_value is not None:
                    # File field
                    files["file"] = field_value

        return self.api_client.request(
            type_=dict[str, Any], method="POST", url="/api/v1/test_run_executions/file_upload/", data=data, files=files
        )

    def _build_for_export_test_run_execution_api_v1_test_run_executions__id__export_get(
        self, id: int, download: bool | None = None
    ) -> Coroutine[Any, Any, m.ExportedTestRunExecution]:
        """
        Export Test Run Execution
        """
        path_params = {"id": str(id)}

        query_params = {}
        if download is not None:
            query_params["download"] = str(download)

        return self.api_client.request(
            type_=m.ExportedTestRunExecution,
            method="GET",
            url="/api/v1/test_run_executions/{id}/export",
            path_params=path_params,
            params=query_params,
        )

    def _build_for_import_test_run_execution_api_v1_test_run_executions_import_post(
        self, body: m.BodyImportTestRunExecutionApiV1TestRunExecutionsImportPost, project_id: int
    ) -> Coroutine[Any, Any, m.TestRunExecutionWithChildren]:
        """
        Import Test Run Execution
        """
        query_params = {"project_id": str(project_id)}

        files: dict[str, IO[Any]] = {}
        data: dict[str, Any] = {}

        # Process body fields to populate files and data dictionaries
        if body is not None:
            # Process field: import_file
            if hasattr(body, "import_file"):
                field_value = getattr(body, "import_file")
                if field_value is not None:
                    # File field
                    files["import_file"] = field_value

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="POST",
            url="/api/v1/test_run_executions/import",
            params=query_params,
            data=data,
            files=files,
        )

    def _build_for_generate_summary_log_api_v1_test_run_executions__id__performance_summary_post(
        self, id: int, project_id: int
    ) -> Coroutine[Any, Any, dict[str, Any]]:
        """
        Generate Summary Log
        """
        path_params = {"id": str(id)}

        query_params = {"project_id": str(project_id)}

        return self.api_client.request(
            type_=dict[str, Any],
            method="POST",
            url="/api/v1/test_run_executions/{id}/performance_summary",
            path_params=path_params,
            params=query_params,
        )


class AsyncTestRunExecutionsApi(_TestRunExecutionsApi):
    async def read_test_run_executions_api_v1_test_run_executions__get(
        self,
        project_id: int | None = None,
        archived: bool | None = None,
        search_query: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        sort_order: str | None = None,
    ) -> list[m.TestRunExecutionWithStats]:
        """
        Read Test Run Executions
        """
        return await self._build_for_read_test_run_executions_api_v1_test_run_executions__get(
            project_id=project_id,
            archived=archived,
            search_query=search_query,
            skip=skip,
            limit=limit,
            sort_order=sort_order,
        )

    async def create_test_run_execution_api_v1_test_run_executions__post(
        self, body: m.BodyCreateTestRunExecutionApiV1TestRunExecutionsPost, certification_mode: bool | None = None
    ) -> m.TestRunExecutionWithChildren:
        """
        Create Test Run Execution
        """
        return await self._build_for_create_test_run_execution_api_v1_test_run_executions__post(
            body=body, certification_mode=certification_mode
        )

    async def create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
        self, body: m.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost
    ) -> m.TestRunExecutionWithChildren:
        """
        Create Cli Test Run Execution
        """
        return await self._build_for_create_cli_test_run_execution_api_v1_test_run_executions_cli_post(body=body)

    async def rename_test_run_execution_api_v1_test_run_executions__id__rename_put(
        self, id: int, new_execution_name: str
    ) -> m.TestRunExecutionWithChildren:
        """
        Rename Test Run Execution
        """
        return await self._build_for_rename_test_run_execution_api_v1_test_run_executions__id__rename_put(
            id=id, new_execution_name=new_execution_name
        )

    async def abort_testing_api_v1_test_run_executions_abort_testing_post(self) -> dict[str, str]:
        """
        Abort Testing
        """
        return await self._build_for_abort_testing_api_v1_test_run_executions_abort_testing_post()

    async def get_test_runner_status_api_v1_test_run_executions_status_get(self) -> m.TestRunnerStatus:
        """
        Get Test Runner Status
        """
        return await self._build_for_get_test_runner_status_api_v1_test_run_executions_status_get()

    async def get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
        self,
        discriminator: str | None = None,
        setup_pin_code: str | None = None,
        version: int | None = None,
        vendor_id: int | None = None,
        product_id: int | None = None,
    ) -> m.ChipServerInfo:
        """
        Get Chip Server Info
        """
        return await self._build_for_get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
            discriminator=discriminator,
            setup_pin_code=setup_pin_code,
            version=version,
            vendor_id=vendor_id,
            product_id=product_id,
        )

    async def read_test_run_execution_api_v1_test_run_executions__id__get(
        self, id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Read Test Run Execution
        """
        return await self._build_for_read_test_run_execution_api_v1_test_run_executions__id__get(id=id)

    async def remove_test_run_execution_api_v1_test_run_executions__id__delete(
        self, id: int
    ) -> m.TestRunExecutionInDBBase:
        """
        Remove Test Run Execution
        """
        return await self._build_for_remove_test_run_execution_api_v1_test_run_executions__id__delete(id=id)

    async def start_test_run_execution_api_v1_test_run_executions__id__start_post(
        self, id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Start Test Run Execution
        """
        return await self._build_for_start_test_run_execution_api_v1_test_run_executions__id__start_post(id=id)

    async def archive_api_v1_test_run_executions__id__archive_post(self, id: int) -> m.TestRunExecution:
        """
        Archive
        """
        return await self._build_for_archive_api_v1_test_run_executions__id__archive_post(id=id)

    async def unarchive_api_v1_test_run_executions__id__unarchive_post(self, id: int) -> m.TestRunExecution:
        """
        Unarchive
        """
        return await self._build_for_unarchive_api_v1_test_run_executions__id__unarchive_post(id=id)

    async def repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post(
        self, id: int, title: str | None = None
    ) -> m.TestRunExecutionWithChildren:
        """
        Repeat Test Run Execution
        """
        return await self._build_for_repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post(
            id=id, title=title
        )

    async def download_log_api_v1_test_run_executions__id__log_get(
        self, id: int, json_entries: bool | None = None, download: bool | None = None
    ) -> None:
        """
        Download Log
        """
        return await self._build_for_download_log_api_v1_test_run_executions__id__log_get(
            id=id, json_entries=json_entries, download=download
        )

    async def download_grouped_log_api_v1_test_run_executions__id__grouped_log_get(self, id: int) -> bytes:
        """
        Download Grouped Log
        """
        return await self._build_for_download_grouped_log_api_v1_test_run_executions__id__grouped_log_get(id=id)

    async def upload_file_api_v1_test_run_executions_file_upload__post(
        self, body: m.BodyUploadFileApiV1TestRunExecutionsFileUploadPost
    ) -> dict[str, Any]:
        """
        Upload File
        """
        return await self._build_for_upload_file_api_v1_test_run_executions_file_upload__post(body=body)

    async def export_test_run_execution_api_v1_test_run_executions__id__export_get(
        self, id: int, download: bool | None = None
    ) -> m.ExportedTestRunExecution:
        """
        Export Test Run Execution
        """
        return await self._build_for_export_test_run_execution_api_v1_test_run_executions__id__export_get(
            id=id, download=download
        )

    async def import_test_run_execution_api_v1_test_run_executions_import_post(
        self, body: m.BodyImportTestRunExecutionApiV1TestRunExecutionsImportPost, project_id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Import Test Run Execution
        """
        return await self._build_for_import_test_run_execution_api_v1_test_run_executions_import_post(
            body=body, project_id=project_id
        )

    async def generate_summary_log_api_v1_test_run_executions__id__performance_summary_post(
        self, id: int, project_id: int
    ) -> dict[str, Any]:
        """
        Generate Summary Log
        """
        return await self._build_for_generate_summary_log_api_v1_test_run_executions__id__performance_summary_post(
            id=id, project_id=project_id
        )


class SyncTestRunExecutionsApi(_TestRunExecutionsApi):
    def read_test_run_executions_api_v1_test_run_executions__get(
        self,
        project_id: int | None = None,
        archived: bool | None = None,
        search_query: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        sort_order: str | None = None,
    ) -> list[m.TestRunExecutionWithStats]:
        """
        Read Test Run Executions
        """
        coroutine = self._build_for_read_test_run_executions_api_v1_test_run_executions__get(
            project_id=project_id,
            archived=archived,
            search_query=search_query,
            skip=skip,
            limit=limit,
            sort_order=sort_order,
        )
        return get_event_loop().run_until_complete(coroutine)

    def create_test_run_execution_api_v1_test_run_executions__post(
        self, body: m.BodyCreateTestRunExecutionApiV1TestRunExecutionsPost, certification_mode: bool | None = None
    ) -> m.TestRunExecutionWithChildren:
        """
        Create Test Run Execution
        """
        coroutine = self._build_for_create_test_run_execution_api_v1_test_run_executions__post(
            body=body, certification_mode=certification_mode
        )
        return get_event_loop().run_until_complete(coroutine)

    def create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
        self, body: m.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost
    ) -> m.TestRunExecutionWithChildren:
        """
        Create Cli Test Run Execution
        """
        coroutine = self._build_for_create_cli_test_run_execution_api_v1_test_run_executions_cli_post(body=body)
        return get_event_loop().run_until_complete(coroutine)

    def rename_test_run_execution_api_v1_test_run_executions__id__rename_put(
        self, id: int, new_execution_name: str
    ) -> m.TestRunExecutionWithChildren:
        """
        Rename Test Run Execution
        """
        coroutine = self._build_for_rename_test_run_execution_api_v1_test_run_executions__id__rename_put(
            id=id, new_execution_name=new_execution_name
        )
        return get_event_loop().run_until_complete(coroutine)

    def abort_testing_api_v1_test_run_executions_abort_testing_post(self) -> dict[str, str]:
        """
        Abort Testing
        """
        coroutine = self._build_for_abort_testing_api_v1_test_run_executions_abort_testing_post()
        return get_event_loop().run_until_complete(coroutine)

    def get_test_runner_status_api_v1_test_run_executions_status_get(self) -> m.TestRunnerStatus:
        """
        Get Test Runner Status
        """
        coroutine = self._build_for_get_test_runner_status_api_v1_test_run_executions_status_get()
        return get_event_loop().run_until_complete(coroutine)

    def get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
        self,
        discriminator: str | None = None,
        setup_pin_code: str | None = None,
        version: int | None = None,
        vendor_id: int | None = None,
        product_id: int | None = None,
    ) -> m.ChipServerInfo:
        """
        Get Chip Server Info
        """
        coroutine = self._build_for_get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
            discriminator=discriminator,
            setup_pin_code=setup_pin_code,
            version=version,
            vendor_id=vendor_id,
            product_id=product_id,
        )
        return get_event_loop().run_until_complete(coroutine)

    def read_test_run_execution_api_v1_test_run_executions__id__get(self, id: int) -> m.TestRunExecutionWithChildren:
        """
        Read Test Run Execution
        """
        coroutine = self._build_for_read_test_run_execution_api_v1_test_run_executions__id__get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def remove_test_run_execution_api_v1_test_run_executions__id__delete(self, id: int) -> m.TestRunExecutionInDBBase:
        """
        Remove Test Run Execution
        """
        coroutine = self._build_for_remove_test_run_execution_api_v1_test_run_executions__id__delete(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def start_test_run_execution_api_v1_test_run_executions__id__start_post(
        self, id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Start Test Run Execution
        """
        coroutine = self._build_for_start_test_run_execution_api_v1_test_run_executions__id__start_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def archive_api_v1_test_run_executions__id__archive_post(self, id: int) -> m.TestRunExecution:
        """
        Archive
        """
        coroutine = self._build_for_archive_api_v1_test_run_executions__id__archive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def unarchive_api_v1_test_run_executions__id__unarchive_post(self, id: int) -> m.TestRunExecution:
        """
        Unarchive
        """
        coroutine = self._build_for_unarchive_api_v1_test_run_executions__id__unarchive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post(
        self, id: int, title: str | None = None
    ) -> m.TestRunExecutionWithChildren:
        """
        Repeat Test Run Execution
        """
        coroutine = self._build_for_repeat_test_run_execution_api_v1_test_run_executions__id__repeat_post(
            id=id, title=title
        )
        return get_event_loop().run_until_complete(coroutine)

    def download_log_api_v1_test_run_executions__id__log_get(
        self, id: int, json_entries: bool | None = None, download: bool | None = None
    ) -> None:
        """
        Download Log
        """
        coroutine = self._build_for_download_log_api_v1_test_run_executions__id__log_get(
            id=id, json_entries=json_entries, download=download
        )
        return get_event_loop().run_until_complete(coroutine)

    def download_grouped_log_api_v1_test_run_executions__id__grouped_log_get(self, id: int) -> bytes:
        """
        Download Grouped Log
        """
        coroutine = self._build_for_download_grouped_log_api_v1_test_run_executions__id__grouped_log_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def upload_file_api_v1_test_run_executions_file_upload__post(
        self, body: m.BodyUploadFileApiV1TestRunExecutionsFileUploadPost
    ) -> dict[str, Any]:
        """
        Upload File
        """
        coroutine = self._build_for_upload_file_api_v1_test_run_executions_file_upload__post(body=body)
        return get_event_loop().run_until_complete(coroutine)

    def export_test_run_execution_api_v1_test_run_executions__id__export_get(
        self, id: int, download: bool | None = None
    ) -> m.ExportedTestRunExecution:
        """
        Export Test Run Execution
        """
        coroutine = self._build_for_export_test_run_execution_api_v1_test_run_executions__id__export_get(
            id=id, download=download
        )
        return get_event_loop().run_until_complete(coroutine)

    def import_test_run_execution_api_v1_test_run_executions_import_post(
        self, body: m.BodyImportTestRunExecutionApiV1TestRunExecutionsImportPost, project_id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Import Test Run Execution
        """
        coroutine = self._build_for_import_test_run_execution_api_v1_test_run_executions_import_post(
            body=body, project_id=project_id
        )
        return get_event_loop().run_until_complete(coroutine)

    def generate_summary_log_api_v1_test_run_executions__id__performance_summary_post(
        self, id: int, project_id: int
    ) -> dict[str, Any]:
        """
        Generate Summary Log
        """
        coroutine = self._build_for_generate_summary_log_api_v1_test_run_executions__id__performance_summary_post(
            id=id, project_id=project_id
        )
        return get_event_loop().run_until_complete(coroutine)
