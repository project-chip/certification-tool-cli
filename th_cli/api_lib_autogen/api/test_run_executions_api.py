#
# Copyright (c) 2023-2026 Project CHIP Authors
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
from typing import IO, TYPE_CHECKING, Any, Awaitable, Dict, List, Optional

from fastapi.encoders import jsonable_encoder

from th_cli.api_lib_autogen import models as m

if TYPE_CHECKING:
    from th_cli.api_lib_autogen.api_client import ApiClient


class _TestRunExecutionsApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_abort_testing_api_v1_test_run_executions_abort_testing_post(self) -> Awaitable[List[str]]:
        """
        Cancel the current testing
        """
        return self.api_client.request(
            type_=List[str],
            method="POST",
            url="/api/v1/test_run_executions/abort-testing",
        )

    def _build_for_archive_api_v1_test_run_executions_id_archive_post(self, id: int) -> Awaitable[m.TestRunExecution]:
        """
        Archive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was archived
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecution,
            method="POST",
            url="/api/v1/test_run_executions/{id}/archive",
            path_params=path_params,
        )

    def _build_for_create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
        self,
        body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post: m.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost,
    ) -> Awaitable[m.TestRunExecutionWithChildren]:
        """
        Creates a new test run execution on CLI request.    Attention: if both config and execution_config are provided,    only config will be persisted, while execution_config will be for    this execution only.  Args:     test_run_execution_in: Test run execution data     selected_tests: Selected tests to run     config: Configuration parameters that update project (optional, persists)     execution_config: Execution-specific config override (optional, temporary)     pics: PICS configuration (optional)
        """
        body = jsonable_encoder(body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post)

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren, method="POST", url="/api/v1/test_run_executions/cli", json=body
        )

    def _build_for_create_test_run_execution_api_v1_test_run_executions_post(
        self,
        body_create_test_run_execution_api_v1_test_run_executions_post: m.BodyCreateTestRunExecutionApiV1TestRunExecutionsPost,
        certification_mode: Optional[bool] = None,
    ) -> Awaitable[m.TestRunExecutionWithChildren]:
        """
        Create a new test run execution.
        """
        query_params = {}
        if certification_mode is not None:
            query_params["certification_mode"] = str(certification_mode)

        body = jsonable_encoder(body_create_test_run_execution_api_v1_test_run_executions_post)

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="POST",
            url="/api/v1/test_run_executions/",
            params=query_params,
            json=body,
        )

    def _build_for_download_grouped_log_api_v1_test_run_executions_id_grouped_log_get(self, id: int) -> Awaitable[None]:
        """
        Download the logs from a test run, grouped by test case state.  Args:     id (int): ID of the TestRunExectution the log is requested for  Raises:     HTTPException: If there's no TestRunExectution with the given ID  Returns:     StreamingResponse: .zip file containing: one file with the list of test cases     for each state; one file with the logs from the executed test suites; one file     per state with the logs from all test cases that finished with that state
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=None,
            method="GET",
            url="/api/v1/test_run_executions/{id}/grouped-log",
            path_params=path_params,
        )

    def _build_for_download_log_api_v1_test_run_executions_id_log_get(
        self, id: int, json_entries: Optional[bool] = None, download: Optional[bool] = None
    ) -> Awaitable[None]:
        """
        Download the logs from a test run.   Args:     id (int): Id of the TestRunExectution the log is requested for     json_entries (bool, optional): When set, return each log line as a json object     download (bool, optional): When set, return as attachment
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

    def _build_for_export_test_run_execution_api_v1_test_run_executions_id_export_get(
        self, id: int, download: Optional[bool] = None
    ) -> Awaitable[m.ExportedTestRunExecution]:
        """
        Exports a test run execution by the given ID.
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

    def _build_for_generate_summary_log_api_v1_test_run_executions_id_performance_summary_post(
        self, id: int, project_id: int
    ) -> Awaitable[object]:
        """
        Imports a test run execution to the the given project_id.
        """
        path_params = {"id": str(id)}

        query_params = {"project_id": str(project_id)}

        return self.api_client.request(
            type_=object,
            method="POST",
            url="/api/v1/test_run_executions/{id}/performance_summary",
            path_params=path_params,
            params=query_params,
        )

    def _build_for_get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
        self,
        discriminator: Optional[str] = None,
        setup_pin_code: Optional[str] = None,
        version: Optional[int] = None,
        vendor_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> Awaitable[m.ChipServerInfo]:
        """
        Retrieve ChipServer node ID information and generate manual pairing code.  Note: Manual pairing code generation requires the SDK container to be running. If called before the SDK container starts, manual_pairing_code will be None.  Args:     discriminator: Device discriminator (optional)     setup_pin_code: Setup PIN code (optional)     version: Version number (default: 0)     vendor_id: Vendor ID (default: 0)     product_id: Product ID (default: 0)  Returns:     ChipServerInfo: Contains node_id, node_id_hex, and optional manual_pairing_code.
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

    def _build_for_get_test_runner_status_api_v1_test_run_executions_status_get(self) -> Awaitable[m.TestRunnerStatus]:
        """
        Retrieve status of the Test Engine.  When the Test Engine is actively running the status will include the current test_run and the details of the states.
        """
        return self.api_client.request(
            type_=m.TestRunnerStatus,
            method="GET",
            url="/api/v1/test_run_executions/status",
        )

    def _build_for_import_test_run_execution_api_v1_test_run_executions_import_post(
        self, project_id: int, import_file: IO[Any]
    ) -> Awaitable[m.TestRunExecutionWithChildren]:
        """
        Imports a test run execution to the the given project_id.
        """
        query_params = {"project_id": str(project_id)}

        files: Dict[str, IO[Any]] = {}  # noqa F841
        data: Dict[str, Any] = {}  # noqa F841
        files["import_file"] = import_file

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="POST",
            url="/api/v1/test_run_executions/import",
            params=query_params,
            data=data,
            files=files,
        )

    def _build_for_read_test_run_execution_api_v1_test_run_executions_id_get(
        self, id: int
    ) -> Awaitable[m.TestRunExecutionWithChildren]:
        """
        Get test run by ID, including state on all children
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="GET",
            url="/api/v1/test_run_executions/{id}",
            path_params=path_params,
        )

    def _build_for_read_test_run_executions_api_v1_test_run_executions_get(
        self,
        project_id: Optional[int] = None,
        archived: Optional[bool] = None,
        search_query: Optional[str] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_order: Optional[str] = None,
    ) -> Awaitable[List[m.TestRunExecutionWithStats]]:
        """
        Retrieve test runs, including statistics.  Args:     project_id: Filter test runs by project.     archived: Get archived test runs, when true will return archived         test runs only, when false only non-archived test runs are returned.     skip: Pagination offset.     limit: Max number of records to return. Set to 0 to return all results.     sort_order: Sort order for results. Either \"asc\" or \"desc\". Defaults to \"asc\".         Results are sorted by ID.  Returns:     List of test runs with execution statistics.
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
            type_=List[m.TestRunExecutionWithStats],
            method="GET",
            url="/api/v1/test_run_executions/",
            params=query_params,
        )

    def _build_for_remove_test_run_execution_api_v1_test_run_executions_id_delete(
        self, id: int
    ) -> Awaitable[m.TestRunExecutionInDBBase]:
        """
        Remove test run execution
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecutionInDBBase,
            method="DELETE",
            url="/api/v1/test_run_executions/{id}",
            path_params=path_params,
        )

    def _build_for_rename_test_run_execution_api_v1_test_run_executions_id_rename_put(
        self, id: int, new_execution_name: str
    ) -> Awaitable[m.TestRunExecutionWithChildren]:
        """
        Rename the name of a test run execution.
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

    def _build_for_repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post(
        self, id: int, title: Optional[str] = None
    ) -> Awaitable[m.TestRunExecutionWithChildren]:
        """
        Repeat a test run execution by id.  Args:     id (int): test run execution id     title (str): Optional title to the repeated test run execution. If not provided,         the old title will be used with the date and time updated.  Raises:     HTTPException: if no test run execution exists for the provided id  Returns:     TestRunExecution: new test run execution with the same test cases from id
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

    def _build_for_start_test_run_execution_api_v1_test_run_executions_id_start_post(
        self, id: int
    ) -> Awaitable[m.TestRunExecutionWithChildren]:
        """
        Start a test run by ID
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecutionWithChildren,
            method="POST",
            url="/api/v1/test_run_executions/{id}/start",
            path_params=path_params,
        )

    def _build_for_unarchive_api_v1_test_run_executions_id_unarchive_post(
        self, id: int
    ) -> Awaitable[m.TestRunExecution]:
        """
        Unarchive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was unarchived
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.TestRunExecution,
            method="POST",
            url="/api/v1/test_run_executions/{id}/unarchive",
            path_params=path_params,
        )

    def _build_for_upload_file_api_v1_test_run_executions_file_upload_post(self, file: IO[Any]) -> Awaitable[object]:
        """
        Upload a file to the specified path of the current test run.  Args:     file: The file to upload.
        """
        files: Dict[str, IO[Any]] = {}  # noqa F841
        data: Dict[str, Any] = {}  # noqa F841
        files["file"] = file

        return self.api_client.request(
            type_=object, method="POST", url="/api/v1/test_run_executions/file_upload/", data=data, files=files
        )


class AsyncTestRunExecutionsApi(_TestRunExecutionsApi):
    async def abort_testing_api_v1_test_run_executions_abort_testing_post(self) -> List[str]:
        """
        Cancel the current testing
        """
        return await self._build_for_abort_testing_api_v1_test_run_executions_abort_testing_post()

    async def archive_api_v1_test_run_executions_id_archive_post(self, id: int) -> m.TestRunExecution:
        """
        Archive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was archived
        """
        return await self._build_for_archive_api_v1_test_run_executions_id_archive_post(id=id)

    async def create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
        self,
        body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post: m.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost,
    ) -> m.TestRunExecutionWithChildren:
        """
        Creates a new test run execution on CLI request.    Attention: if both config and execution_config are provided,    only config will be persisted, while execution_config will be for    this execution only.  Args:     test_run_execution_in: Test run execution data     selected_tests: Selected tests to run     config: Configuration parameters that update project (optional, persists)     execution_config: Execution-specific config override (optional, temporary)     pics: PICS configuration (optional)
        """
        return await self._build_for_create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
            body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post=body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        )

    async def create_test_run_execution_api_v1_test_run_executions_post(
        self,
        body_create_test_run_execution_api_v1_test_run_executions_post: m.BodyCreateTestRunExecutionApiV1TestRunExecutionsPost,
        certification_mode: Optional[bool] = None,
    ) -> m.TestRunExecutionWithChildren:
        """
        Create a new test run execution.
        """
        return await self._build_for_create_test_run_execution_api_v1_test_run_executions_post(
            body_create_test_run_execution_api_v1_test_run_executions_post=body_create_test_run_execution_api_v1_test_run_executions_post,
            certification_mode=certification_mode,
        )

    async def download_grouped_log_api_v1_test_run_executions_id_grouped_log_get(self, id: int) -> None:
        """
        Download the logs from a test run, grouped by test case state.  Args:     id (int): ID of the TestRunExectution the log is requested for  Raises:     HTTPException: If there's no TestRunExectution with the given ID  Returns:     StreamingResponse: .zip file containing: one file with the list of test cases     for each state; one file with the logs from the executed test suites; one file     per state with the logs from all test cases that finished with that state
        """
        return await self._build_for_download_grouped_log_api_v1_test_run_executions_id_grouped_log_get(id=id)

    async def download_log_api_v1_test_run_executions_id_log_get(
        self, id: int, json_entries: Optional[bool] = None, download: Optional[bool] = None
    ) -> None:
        """
        Download the logs from a test run.   Args:     id (int): Id of the TestRunExectution the log is requested for     json_entries (bool, optional): When set, return each log line as a json object     download (bool, optional): When set, return as attachment
        """
        return await self._build_for_download_log_api_v1_test_run_executions_id_log_get(
            id=id, json_entries=json_entries, download=download
        )

    async def export_test_run_execution_api_v1_test_run_executions_id_export_get(
        self, id: int, download: Optional[bool] = None
    ) -> m.ExportedTestRunExecution:
        """
        Exports a test run execution by the given ID.
        """
        return await self._build_for_export_test_run_execution_api_v1_test_run_executions_id_export_get(
            id=id, download=download
        )

    async def generate_summary_log_api_v1_test_run_executions_id_performance_summary_post(
        self, id: int, project_id: int
    ) -> object:
        """
        Imports a test run execution to the the given project_id.
        """
        return await self._build_for_generate_summary_log_api_v1_test_run_executions_id_performance_summary_post(
            id=id, project_id=project_id
        )

    async def get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
        self,
        discriminator: Optional[str] = None,
        setup_pin_code: Optional[str] = None,
        version: Optional[int] = None,
        vendor_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> m.ChipServerInfo:
        """
        Retrieve ChipServer node ID information and generate manual pairing code.  Note: Manual pairing code generation requires the SDK container to be running. If called before the SDK container starts, manual_pairing_code will be None.  Args:     discriminator: Device discriminator (optional)     setup_pin_code: Setup PIN code (optional)     version: Version number (default: 0)     vendor_id: Vendor ID (default: 0)     product_id: Product ID (default: 0)  Returns:     ChipServerInfo: Contains node_id, node_id_hex, and optional manual_pairing_code.
        """
        return await self._build_for_get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
            discriminator=discriminator,
            setup_pin_code=setup_pin_code,
            version=version,
            vendor_id=vendor_id,
            product_id=product_id,
        )

    async def get_test_runner_status_api_v1_test_run_executions_status_get(self) -> m.TestRunnerStatus:
        """
        Retrieve status of the Test Engine.  When the Test Engine is actively running the status will include the current test_run and the details of the states.
        """
        return await self._build_for_get_test_runner_status_api_v1_test_run_executions_status_get()

    async def import_test_run_execution_api_v1_test_run_executions_import_post(
        self, project_id: int, import_file: IO[Any]
    ) -> m.TestRunExecutionWithChildren:
        """
        Imports a test run execution to the the given project_id.
        """
        return await self._build_for_import_test_run_execution_api_v1_test_run_executions_import_post(
            project_id=project_id, import_file=import_file
        )

    async def read_test_run_execution_api_v1_test_run_executions_id_get(
        self, id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Get test run by ID, including state on all children
        """
        return await self._build_for_read_test_run_execution_api_v1_test_run_executions_id_get(id=id)

    async def read_test_run_executions_api_v1_test_run_executions_get(
        self,
        project_id: Optional[int] = None,
        archived: Optional[bool] = None,
        search_query: Optional[str] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_order: Optional[str] = None,
    ) -> List[m.TestRunExecutionWithStats]:
        """
        Retrieve test runs, including statistics.  Args:     project_id: Filter test runs by project.     archived: Get archived test runs, when true will return archived         test runs only, when false only non-archived test runs are returned.     skip: Pagination offset.     limit: Max number of records to return. Set to 0 to return all results.     sort_order: Sort order for results. Either \"asc\" or \"desc\". Defaults to \"asc\".         Results are sorted by ID.  Returns:     List of test runs with execution statistics.
        """
        return await self._build_for_read_test_run_executions_api_v1_test_run_executions_get(
            project_id=project_id,
            archived=archived,
            search_query=search_query,
            skip=skip,
            limit=limit,
            sort_order=sort_order,
        )

    async def remove_test_run_execution_api_v1_test_run_executions_id_delete(
        self, id: int
    ) -> m.TestRunExecutionInDBBase:
        """
        Remove test run execution
        """
        return await self._build_for_remove_test_run_execution_api_v1_test_run_executions_id_delete(id=id)

    async def rename_test_run_execution_api_v1_test_run_executions_id_rename_put(
        self, id: int, new_execution_name: str
    ) -> m.TestRunExecutionWithChildren:
        """
        Rename the name of a test run execution.
        """
        return await self._build_for_rename_test_run_execution_api_v1_test_run_executions_id_rename_put(
            id=id, new_execution_name=new_execution_name
        )

    async def repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post(
        self, id: int, title: Optional[str] = None
    ) -> m.TestRunExecutionWithChildren:
        """
        Repeat a test run execution by id.  Args:     id (int): test run execution id     title (str): Optional title to the repeated test run execution. If not provided,         the old title will be used with the date and time updated.  Raises:     HTTPException: if no test run execution exists for the provided id  Returns:     TestRunExecution: new test run execution with the same test cases from id
        """
        return await self._build_for_repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post(
            id=id, title=title
        )

    async def start_test_run_execution_api_v1_test_run_executions_id_start_post(
        self, id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Start a test run by ID
        """
        return await self._build_for_start_test_run_execution_api_v1_test_run_executions_id_start_post(id=id)

    async def unarchive_api_v1_test_run_executions_id_unarchive_post(self, id: int) -> m.TestRunExecution:
        """
        Unarchive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was unarchived
        """
        return await self._build_for_unarchive_api_v1_test_run_executions_id_unarchive_post(id=id)

    async def upload_file_api_v1_test_run_executions_file_upload_post(self, file: IO[Any]) -> object:
        """
        Upload a file to the specified path of the current test run.  Args:     file: The file to upload.
        """
        return await self._build_for_upload_file_api_v1_test_run_executions_file_upload_post(file=file)


class SyncTestRunExecutionsApi(_TestRunExecutionsApi):
    def abort_testing_api_v1_test_run_executions_abort_testing_post(self) -> List[str]:
        """
        Cancel the current testing
        """
        coroutine = self._build_for_abort_testing_api_v1_test_run_executions_abort_testing_post()
        return get_event_loop().run_until_complete(coroutine)

    def archive_api_v1_test_run_executions_id_archive_post(self, id: int) -> m.TestRunExecution:
        """
        Archive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was archived
        """
        coroutine = self._build_for_archive_api_v1_test_run_executions_id_archive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
        self,
        body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post: m.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost,
    ) -> m.TestRunExecutionWithChildren:
        """
        Creates a new test run execution on CLI request.    Attention: if both config and execution_config are provided,    only config will be persisted, while execution_config will be for    this execution only.  Args:     test_run_execution_in: Test run execution data     selected_tests: Selected tests to run     config: Configuration parameters that update project (optional, persists)     execution_config: Execution-specific config override (optional, temporary)     pics: PICS configuration (optional)
        """
        coroutine = self._build_for_create_cli_test_run_execution_api_v1_test_run_executions_cli_post(
            body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post=body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post
        )
        return get_event_loop().run_until_complete(coroutine)

    def create_test_run_execution_api_v1_test_run_executions_post(
        self,
        body_create_test_run_execution_api_v1_test_run_executions_post: m.BodyCreateTestRunExecutionApiV1TestRunExecutionsPost,
        certification_mode: Optional[bool] = None,
    ) -> m.TestRunExecutionWithChildren:
        """
        Create a new test run execution.
        """
        coroutine = self._build_for_create_test_run_execution_api_v1_test_run_executions_post(
            body_create_test_run_execution_api_v1_test_run_executions_post=body_create_test_run_execution_api_v1_test_run_executions_post,
            certification_mode=certification_mode,
        )
        return get_event_loop().run_until_complete(coroutine)

    def download_grouped_log_api_v1_test_run_executions_id_grouped_log_get(self, id: int) -> None:
        """
        Download the logs from a test run, grouped by test case state.  Args:     id (int): ID of the TestRunExectution the log is requested for  Raises:     HTTPException: If there's no TestRunExectution with the given ID  Returns:     StreamingResponse: .zip file containing: one file with the list of test cases     for each state; one file with the logs from the executed test suites; one file     per state with the logs from all test cases that finished with that state
        """
        coroutine = self._build_for_download_grouped_log_api_v1_test_run_executions_id_grouped_log_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def download_log_api_v1_test_run_executions_id_log_get(
        self, id: int, json_entries: Optional[bool] = None, download: Optional[bool] = None
    ) -> None:
        """
        Download the logs from a test run.   Args:     id (int): Id of the TestRunExectution the log is requested for     json_entries (bool, optional): When set, return each log line as a json object     download (bool, optional): When set, return as attachment
        """
        coroutine = self._build_for_download_log_api_v1_test_run_executions_id_log_get(
            id=id, json_entries=json_entries, download=download
        )
        return get_event_loop().run_until_complete(coroutine)

    def export_test_run_execution_api_v1_test_run_executions_id_export_get(
        self, id: int, download: Optional[bool] = None
    ) -> m.ExportedTestRunExecution:
        """
        Exports a test run execution by the given ID.
        """
        coroutine = self._build_for_export_test_run_execution_api_v1_test_run_executions_id_export_get(
            id=id, download=download
        )
        return get_event_loop().run_until_complete(coroutine)

    def generate_summary_log_api_v1_test_run_executions_id_performance_summary_post(
        self, id: int, project_id: int
    ) -> object:
        """
        Imports a test run execution to the the given project_id.
        """
        coroutine = self._build_for_generate_summary_log_api_v1_test_run_executions_id_performance_summary_post(
            id=id, project_id=project_id
        )
        return get_event_loop().run_until_complete(coroutine)

    def get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
        self,
        discriminator: Optional[str] = None,
        setup_pin_code: Optional[str] = None,
        version: Optional[int] = None,
        vendor_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> m.ChipServerInfo:
        """
        Retrieve ChipServer node ID information and generate manual pairing code.  Note: Manual pairing code generation requires the SDK container to be running. If called before the SDK container starts, manual_pairing_code will be None.  Args:     discriminator: Device discriminator (optional)     setup_pin_code: Setup PIN code (optional)     version: Version number (default: 0)     vendor_id: Vendor ID (default: 0)     product_id: Product ID (default: 0)  Returns:     ChipServerInfo: Contains node_id, node_id_hex, and optional manual_pairing_code.
        """
        coroutine = self._build_for_get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(
            discriminator=discriminator,
            setup_pin_code=setup_pin_code,
            version=version,
            vendor_id=vendor_id,
            product_id=product_id,
        )
        return get_event_loop().run_until_complete(coroutine)

    def get_test_runner_status_api_v1_test_run_executions_status_get(self) -> m.TestRunnerStatus:
        """
        Retrieve status of the Test Engine.  When the Test Engine is actively running the status will include the current test_run and the details of the states.
        """
        coroutine = self._build_for_get_test_runner_status_api_v1_test_run_executions_status_get()
        return get_event_loop().run_until_complete(coroutine)

    def import_test_run_execution_api_v1_test_run_executions_import_post(
        self, project_id: int, import_file: IO[Any]
    ) -> m.TestRunExecutionWithChildren:
        """
        Imports a test run execution to the the given project_id.
        """
        coroutine = self._build_for_import_test_run_execution_api_v1_test_run_executions_import_post(
            project_id=project_id, import_file=import_file
        )
        return get_event_loop().run_until_complete(coroutine)

    def read_test_run_execution_api_v1_test_run_executions_id_get(self, id: int) -> m.TestRunExecutionWithChildren:
        """
        Get test run by ID, including state on all children
        """
        coroutine = self._build_for_read_test_run_execution_api_v1_test_run_executions_id_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def read_test_run_executions_api_v1_test_run_executions_get(
        self,
        project_id: Optional[int] = None,
        archived: Optional[bool] = None,
        search_query: Optional[str] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_order: Optional[str] = None,
    ) -> List[m.TestRunExecutionWithStats]:
        """
        Retrieve test runs, including statistics.  Args:     project_id: Filter test runs by project.     archived: Get archived test runs, when true will return archived         test runs only, when false only non-archived test runs are returned.     skip: Pagination offset.     limit: Max number of records to return. Set to 0 to return all results.     sort_order: Sort order for results. Either \"asc\" or \"desc\". Defaults to \"asc\".         Results are sorted by ID.  Returns:     List of test runs with execution statistics.
        """
        coroutine = self._build_for_read_test_run_executions_api_v1_test_run_executions_get(
            project_id=project_id,
            archived=archived,
            search_query=search_query,
            skip=skip,
            limit=limit,
            sort_order=sort_order,
        )
        return get_event_loop().run_until_complete(coroutine)

    def remove_test_run_execution_api_v1_test_run_executions_id_delete(self, id: int) -> m.TestRunExecutionInDBBase:
        """
        Remove test run execution
        """
        coroutine = self._build_for_remove_test_run_execution_api_v1_test_run_executions_id_delete(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def rename_test_run_execution_api_v1_test_run_executions_id_rename_put(
        self, id: int, new_execution_name: str
    ) -> m.TestRunExecutionWithChildren:
        """
        Rename the name of a test run execution.
        """
        coroutine = self._build_for_rename_test_run_execution_api_v1_test_run_executions_id_rename_put(
            id=id, new_execution_name=new_execution_name
        )
        return get_event_loop().run_until_complete(coroutine)

    def repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post(
        self, id: int, title: Optional[str] = None
    ) -> m.TestRunExecutionWithChildren:
        """
        Repeat a test run execution by id.  Args:     id (int): test run execution id     title (str): Optional title to the repeated test run execution. If not provided,         the old title will be used with the date and time updated.  Raises:     HTTPException: if no test run execution exists for the provided id  Returns:     TestRunExecution: new test run execution with the same test cases from id
        """
        coroutine = self._build_for_repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post(
            id=id, title=title
        )
        return get_event_loop().run_until_complete(coroutine)

    def start_test_run_execution_api_v1_test_run_executions_id_start_post(
        self, id: int
    ) -> m.TestRunExecutionWithChildren:
        """
        Start a test run by ID
        """
        coroutine = self._build_for_start_test_run_execution_api_v1_test_run_executions_id_start_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def unarchive_api_v1_test_run_executions_id_unarchive_post(self, id: int) -> m.TestRunExecution:
        """
        Unarchive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was unarchived
        """
        coroutine = self._build_for_unarchive_api_v1_test_run_executions_id_unarchive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def upload_file_api_v1_test_run_executions_file_upload_post(self, file: IO[Any]) -> object:
        """
        Upload a file to the specified path of the current test run.  Args:     file: The file to upload.
        """
        coroutine = self._build_for_upload_file_api_v1_test_run_executions_file_upload_post(file=file)
        return get_event_loop().run_until_complete(coroutine)
