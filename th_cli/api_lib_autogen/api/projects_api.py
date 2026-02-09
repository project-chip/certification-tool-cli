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


class _ProjectsApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_applicable_test_cases_api_v1_projects_id_applicable_test_cases_get(
        self, id: int
    ) -> Awaitable[m.PICSApplicableTestCases]:
        """
        Retrieve list of applicable test cases based on project identifier.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     PICSApplicableTestCases: List of applicable test cases
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.PICSApplicableTestCases,
            method="GET",
            url="/api/v1/projects/{id}/applicable_test_cases",
            path_params=path_params,
        )

    def _build_for_archive_project_api_v1_projects_id_archive_post(self, id: int) -> Awaitable[m.Project]:
        """
        Archive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was archived
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project,
            method="POST",
            url="/api/v1/projects/{id}/archive",
            path_params=path_params,
        )

    def _build_for_create_project_api_v1_projects_post(self, project_create: m.ProjectCreate) -> Awaitable[m.Project]:
        """
        Create new project  Args:     project_in (ProjectCreate): Parameters for new project,  see schema for details  Returns:     Project: newly created project record
        """
        body = jsonable_encoder(project_create)

        return self.api_client.request(type_=m.Project, method="POST", url="/api/v1/projects/", json=body)

    def _build_for_default_config_api_v1_projects_default_config_get(
        self,
    ) -> Awaitable[m.ResponseDefaultConfigApiV1ProjectsDefaultConfigGet]:
        """
        Return default configuration for projects.  Returns:     List[Project]: List of projects
        """
        return self.api_client.request(
            type_=m.ResponseDefaultConfigApiV1ProjectsDefaultConfigGet,
            method="GET",
            url="/api/v1/projects/default_config",
        )

    def _build_for_delete_project_api_v1_projects_id_delete(self, id: int) -> Awaitable[m.Project]:
        """
        Delete project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was deleted
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project,
            method="DELETE",
            url="/api/v1/projects/{id}",
            path_params=path_params,
        )

    def _build_for_export_project_config_api_v1_projects_id_export_get(self, id: int) -> Awaitable[m.ProjectCreate]:
        """
        Exports the project config by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     JSONResponse: json representation of the project with the informed project id
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.ProjectCreate,
            method="GET",
            url="/api/v1/projects/{id}/export",
            path_params=path_params,
        )

    def _build_for_importproject_config_api_v1_projects_import_post(self, import_file: IO[Any]) -> Awaitable[m.Project]:
        """
        Imports the project config  Args:     import_file : The project config file to be imported  Raises:     ValidationError: if the imported project config contains invalid information  Returns:     Project: newly created project record
        """
        files: Dict[str, IO[Any]] = {}  # noqa F841
        data: Dict[str, Any] = {}  # noqa F841
        files["import_file"] = import_file

        return self.api_client.request(
            type_=m.Project, method="POST", url="/api/v1/projects/import", data=data, files=files
        )

    def _build_for_read_project_api_v1_projects_id_get(self, id: int) -> Awaitable[m.Project]:
        """
        Lookup project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project,
            method="GET",
            url="/api/v1/projects/{id}",
            path_params=path_params,
        )

    def _build_for_read_projects_api_v1_projects_get(
        self, archived: Optional[bool] = None, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> Awaitable[List[m.Project]]:
        """
        Retrieve list of projects  Args:     archived (bool, optional): Get archived projects, when true will; get archived         projects only, when false only non-archived projects are returned.         Defaults to false.     skip (int, optional): Pagination offset. Defaults to 0.     limit (int, optional): max number of records to return. Defaults to 100.  Returns:     List[Project]: List of projects
        """
        query_params = {}
        if archived is not None:
            query_params["archived"] = str(archived)
        if skip is not None:
            query_params["skip"] = str(skip)
        if limit is not None:
            query_params["limit"] = str(limit)

        return self.api_client.request(
            type_=List[m.Project],
            method="GET",
            url="/api/v1/projects/",
            params=query_params,
        )

    def _build_for_remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete(
        self, id: int, cluster_name: str
    ) -> Awaitable[m.Project]:
        """
        Removes cluster based on given cluster name  Args:     id (int): ID of Project     cluster_name (str): Name of the cluster to delete  Raises:     HTTPException: if no project exists for provided project id  Returns:     models.Project: Project with updated PICS entry
        """
        path_params = {"id": str(id)}

        query_params = {"cluster_name": str(cluster_name)}

        return self.api_client.request(
            type_=m.Project,
            method="DELETE",
            url="/api/v1/projects/{id}/pics_cluster_type",
            path_params=path_params,
            params=query_params,
        )

    def _build_for_unarchive_project_api_v1_projects_id_unarchive_post(self, id: int) -> Awaitable[m.Project]:
        """
        Unarchive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was unarchived
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project,
            method="POST",
            url="/api/v1/projects/{id}/unarchive",
            path_params=path_params,
        )

    def _build_for_update_project_api_v1_projects_id_put(
        self, id: int, project_update: m.ProjectUpdate
    ) -> Awaitable[m.Project]:
        """
        Update an existing project  Args:     id (int): project id     project_in (schemas.ProjectUpdate): projects parameters to be updated  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: updated project record
        """
        path_params = {"id": str(id)}

        body = jsonable_encoder(project_update)

        return self.api_client.request(
            type_=m.Project, method="PUT", url="/api/v1/projects/{id}", path_params=path_params, json=body
        )

    def _build_for_upload_pics_api_v1_projects_id_upload_pics_put(self, id: int, file: IO[Any]) -> Awaitable[m.Project]:
        """
        Upload PICS or dmp-test-skip.xml file of a project based on project identifier.  Args:     id (int): project id     file : the PICS or dmp-test-skip.xml file to upload  Raises:     HTTPException: if no project exists for provided project id (or)                    if the PICS file is invalid  Returns:     Project: project record that was updated with the PICS and dmp_test_skip     information.
        """
        path_params = {"id": str(id)}

        files: Dict[str, IO[Any]] = {}  # noqa F841
        data: Dict[str, Any] = {}  # noqa F841
        files["file"] = file

        return self.api_client.request(
            type_=m.Project,
            method="PUT",
            url="/api/v1/projects/{id}/upload_pics",
            path_params=path_params,
            data=data,
            files=files,
        )


class AsyncProjectsApi(_ProjectsApi):
    async def applicable_test_cases_api_v1_projects_id_applicable_test_cases_get(
        self, id: int
    ) -> m.PICSApplicableTestCases:
        """
        Retrieve list of applicable test cases based on project identifier.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     PICSApplicableTestCases: List of applicable test cases
        """
        return await self._build_for_applicable_test_cases_api_v1_projects_id_applicable_test_cases_get(id=id)

    async def archive_project_api_v1_projects_id_archive_post(self, id: int) -> m.Project:
        """
        Archive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was archived
        """
        return await self._build_for_archive_project_api_v1_projects_id_archive_post(id=id)

    async def create_project_api_v1_projects_post(self, project_create: m.ProjectCreate) -> m.Project:
        """
        Create new project  Args:     project_in (ProjectCreate): Parameters for new project,  see schema for details  Returns:     Project: newly created project record
        """
        return await self._build_for_create_project_api_v1_projects_post(project_create=project_create)

    async def default_config_api_v1_projects_default_config_get(
        self,
    ) -> m.ResponseDefaultConfigApiV1ProjectsDefaultConfigGet:
        """
        Return default configuration for projects.  Returns:     List[Project]: List of projects
        """
        return await self._build_for_default_config_api_v1_projects_default_config_get()

    async def delete_project_api_v1_projects_id_delete(self, id: int) -> m.Project:
        """
        Delete project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was deleted
        """
        return await self._build_for_delete_project_api_v1_projects_id_delete(id=id)

    async def export_project_config_api_v1_projects_id_export_get(self, id: int) -> m.ProjectCreate:
        """
        Exports the project config by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     JSONResponse: json representation of the project with the informed project id
        """
        return await self._build_for_export_project_config_api_v1_projects_id_export_get(id=id)

    async def importproject_config_api_v1_projects_import_post(self, import_file: IO[Any]) -> m.Project:
        """
        Imports the project config  Args:     import_file : The project config file to be imported  Raises:     ValidationError: if the imported project config contains invalid information  Returns:     Project: newly created project record
        """
        return await self._build_for_importproject_config_api_v1_projects_import_post(import_file=import_file)

    async def read_project_api_v1_projects_id_get(self, id: int) -> m.Project:
        """
        Lookup project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record
        """
        return await self._build_for_read_project_api_v1_projects_id_get(id=id)

    async def read_projects_api_v1_projects_get(
        self, archived: Optional[bool] = None, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> List[m.Project]:
        """
        Retrieve list of projects  Args:     archived (bool, optional): Get archived projects, when true will; get archived         projects only, when false only non-archived projects are returned.         Defaults to false.     skip (int, optional): Pagination offset. Defaults to 0.     limit (int, optional): max number of records to return. Defaults to 100.  Returns:     List[Project]: List of projects
        """
        return await self._build_for_read_projects_api_v1_projects_get(archived=archived, skip=skip, limit=limit)

    async def remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete(
        self, id: int, cluster_name: str
    ) -> m.Project:
        """
        Removes cluster based on given cluster name  Args:     id (int): ID of Project     cluster_name (str): Name of the cluster to delete  Raises:     HTTPException: if no project exists for provided project id  Returns:     models.Project: Project with updated PICS entry
        """
        return await self._build_for_remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete(
            id=id, cluster_name=cluster_name
        )

    async def unarchive_project_api_v1_projects_id_unarchive_post(self, id: int) -> m.Project:
        """
        Unarchive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was unarchived
        """
        return await self._build_for_unarchive_project_api_v1_projects_id_unarchive_post(id=id)

    async def update_project_api_v1_projects_id_put(self, id: int, project_update: m.ProjectUpdate) -> m.Project:
        """
        Update an existing project  Args:     id (int): project id     project_in (schemas.ProjectUpdate): projects parameters to be updated  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: updated project record
        """
        return await self._build_for_update_project_api_v1_projects_id_put(id=id, project_update=project_update)

    async def upload_pics_api_v1_projects_id_upload_pics_put(self, id: int, file: IO[Any]) -> m.Project:
        """
        Upload PICS or dmp-test-skip.xml file of a project based on project identifier.  Args:     id (int): project id     file : the PICS or dmp-test-skip.xml file to upload  Raises:     HTTPException: if no project exists for provided project id (or)                    if the PICS file is invalid  Returns:     Project: project record that was updated with the PICS and dmp_test_skip     information.
        """
        return await self._build_for_upload_pics_api_v1_projects_id_upload_pics_put(id=id, file=file)


class SyncProjectsApi(_ProjectsApi):
    def applicable_test_cases_api_v1_projects_id_applicable_test_cases_get(self, id: int) -> m.PICSApplicableTestCases:
        """
        Retrieve list of applicable test cases based on project identifier.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     PICSApplicableTestCases: List of applicable test cases
        """
        coroutine = self._build_for_applicable_test_cases_api_v1_projects_id_applicable_test_cases_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def archive_project_api_v1_projects_id_archive_post(self, id: int) -> m.Project:
        """
        Archive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was archived
        """
        coroutine = self._build_for_archive_project_api_v1_projects_id_archive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def create_project_api_v1_projects_post(self, project_create: m.ProjectCreate) -> m.Project:
        """
        Create new project  Args:     project_in (ProjectCreate): Parameters for new project,  see schema for details  Returns:     Project: newly created project record
        """
        coroutine = self._build_for_create_project_api_v1_projects_post(project_create=project_create)
        return get_event_loop().run_until_complete(coroutine)

    def default_config_api_v1_projects_default_config_get(self) -> m.ResponseDefaultConfigApiV1ProjectsDefaultConfigGet:
        """
        Return default configuration for projects.  Returns:     List[Project]: List of projects
        """
        coroutine = self._build_for_default_config_api_v1_projects_default_config_get()
        return get_event_loop().run_until_complete(coroutine)

    def delete_project_api_v1_projects_id_delete(self, id: int) -> m.Project:
        """
        Delete project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was deleted
        """
        coroutine = self._build_for_delete_project_api_v1_projects_id_delete(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def export_project_config_api_v1_projects_id_export_get(self, id: int) -> m.ProjectCreate:
        """
        Exports the project config by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     JSONResponse: json representation of the project with the informed project id
        """
        coroutine = self._build_for_export_project_config_api_v1_projects_id_export_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def importproject_config_api_v1_projects_import_post(self, import_file: IO[Any]) -> m.Project:
        """
        Imports the project config  Args:     import_file : The project config file to be imported  Raises:     ValidationError: if the imported project config contains invalid information  Returns:     Project: newly created project record
        """
        coroutine = self._build_for_importproject_config_api_v1_projects_import_post(import_file=import_file)
        return get_event_loop().run_until_complete(coroutine)

    def read_project_api_v1_projects_id_get(self, id: int) -> m.Project:
        """
        Lookup project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record
        """
        coroutine = self._build_for_read_project_api_v1_projects_id_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def read_projects_api_v1_projects_get(
        self, archived: Optional[bool] = None, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> List[m.Project]:
        """
        Retrieve list of projects  Args:     archived (bool, optional): Get archived projects, when true will; get archived         projects only, when false only non-archived projects are returned.         Defaults to false.     skip (int, optional): Pagination offset. Defaults to 0.     limit (int, optional): max number of records to return. Defaults to 100.  Returns:     List[Project]: List of projects
        """
        coroutine = self._build_for_read_projects_api_v1_projects_get(archived=archived, skip=skip, limit=limit)
        return get_event_loop().run_until_complete(coroutine)

    def remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete(
        self, id: int, cluster_name: str
    ) -> m.Project:
        """
        Removes cluster based on given cluster name  Args:     id (int): ID of Project     cluster_name (str): Name of the cluster to delete  Raises:     HTTPException: if no project exists for provided project id  Returns:     models.Project: Project with updated PICS entry
        """
        coroutine = self._build_for_remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete(
            id=id, cluster_name=cluster_name
        )
        return get_event_loop().run_until_complete(coroutine)

    def unarchive_project_api_v1_projects_id_unarchive_post(self, id: int) -> m.Project:
        """
        Unarchive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was unarchived
        """
        coroutine = self._build_for_unarchive_project_api_v1_projects_id_unarchive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def update_project_api_v1_projects_id_put(self, id: int, project_update: m.ProjectUpdate) -> m.Project:
        """
        Update an existing project  Args:     id (int): project id     project_in (schemas.ProjectUpdate): projects parameters to be updated  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: updated project record
        """
        coroutine = self._build_for_update_project_api_v1_projects_id_put(id=id, project_update=project_update)
        return get_event_loop().run_until_complete(coroutine)

    def upload_pics_api_v1_projects_id_upload_pics_put(self, id: int, file: IO[Any]) -> m.Project:
        """
        Upload PICS or dmp-test-skip.xml file of a project based on project identifier.  Args:     id (int): project id     file : the PICS or dmp-test-skip.xml file to upload  Raises:     HTTPException: if no project exists for provided project id (or)                    if the PICS file is invalid  Returns:     Project: project record that was updated with the PICS and dmp_test_skip     information.
        """
        coroutine = self._build_for_upload_pics_api_v1_projects_id_upload_pics_put(id=id, file=file)
        return get_event_loop().run_until_complete(coroutine)
