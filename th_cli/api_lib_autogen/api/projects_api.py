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


class _ProjectsApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_read_projects_api_v1_projects__get(
        self, archived: bool | None = None, skip: int | None = None, limit: int | None = None
    ) -> Coroutine[Any, Any, list[m.Project]]:
        """
        Read Projects
        """
        query_params = {}
        if archived is not None:
            query_params["archived"] = str(archived)
        if skip is not None:
            query_params["skip"] = str(skip)
        if limit is not None:
            query_params["limit"] = str(limit)

        return self.api_client.request(
            type_=list[m.Project], method="GET", url="/api/v1/projects/", params=query_params
        )

    def _build_for_create_project_api_v1_projects__post(self, body: m.ProjectCreate) -> Coroutine[Any, Any, m.Project]:
        """
        Create Project
        """
        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(type_=m.Project, method="POST", url="/api/v1/projects/", json=json_body)

    def _build_for_default_config_api_v1_projects_default_config_get(self) -> Coroutine[Any, Any, dict[str, Any]]:
        """
        Default Config
        """
        return self.api_client.request(type_=dict[str, Any], method="GET", url="/api/v1/projects/default_config")

    def _build_for_read_project_api_v1_projects__id__get(self, id: int) -> Coroutine[Any, Any, m.Project]:
        """
        Read Project
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project, method="GET", url="/api/v1/projects/{id}", path_params=path_params
        )

    def _build_for_update_project_api_v1_projects__id__put(
        self, body: m.ProjectUpdate, id: int
    ) -> Coroutine[Any, Any, m.Project]:
        """
        Update Project
        """
        path_params = {"id": str(id)}

        json_body = body.model_dump(mode="json") if hasattr(body, "model_dump") else body

        return self.api_client.request(
            type_=m.Project, method="PUT", url="/api/v1/projects/{id}", path_params=path_params, json=json_body
        )

    def _build_for_delete_project_api_v1_projects__id__delete(self, id: int) -> Coroutine[Any, Any, m.Project]:
        """
        Delete Project
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project, method="DELETE", url="/api/v1/projects/{id}", path_params=path_params
        )

    def _build_for_archive_project_api_v1_projects__id__archive_post(self, id: int) -> Coroutine[Any, Any, m.Project]:
        """
        Archive Project
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project, method="POST", url="/api/v1/projects/{id}/archive", path_params=path_params
        )

    def _build_for_unarchive_project_api_v1_projects__id__unarchive_post(
        self, id: int
    ) -> Coroutine[Any, Any, m.Project]:
        """
        Unarchive Project
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.Project, method="POST", url="/api/v1/projects/{id}/unarchive", path_params=path_params
        )

    def _build_for_upload_pics_api_v1_projects__id__upload_pics_put(
        self, body: m.BodyUploadPicsApiV1ProjectsIdUploadPicsPut, id: int
    ) -> Coroutine[Any, Any, m.Project]:
        """
        Upload Pics
        """
        path_params = {"id": str(id)}

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
            type_=m.Project,
            method="PUT",
            url="/api/v1/projects/{id}/upload_pics",
            path_params=path_params,
            data=data,
            files=files,
        )

    def _build_for_remove_pics_cluster_type_api_v1_projects__id__pics_cluster_type_delete(
        self, id: int, cluster_name: str
    ) -> Coroutine[Any, Any, m.Project]:
        """
        Remove Pics Cluster Type
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

    def _build_for_applicable_test_cases_api_v1_projects__id__applicable_test_cases_get(
        self, id: int
    ) -> Coroutine[Any, Any, m.PICSApplicableTestCases]:
        """
        Applicable Test Cases
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.PICSApplicableTestCases,
            method="GET",
            url="/api/v1/projects/{id}/applicable_test_cases",
            path_params=path_params,
        )

    def _build_for_export_project_config_api_v1_projects__id__export_get(
        self, id: int
    ) -> Coroutine[Any, Any, m.ProjectCreate]:
        """
        Export Project Config
        """
        path_params = {"id": str(id)}

        return self.api_client.request(
            type_=m.ProjectCreate, method="GET", url="/api/v1/projects/{id}/export", path_params=path_params
        )

    def _build_for_importproject_config_api_v1_projects_import_post(
        self, body: m.BodyImportprojectConfigApiV1ProjectsImportPost
    ) -> Coroutine[Any, Any, m.Project]:
        """
        Importproject Config
        """
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
            type_=m.Project, method="POST", url="/api/v1/projects/import", data=data, files=files
        )


class AsyncProjectsApi(_ProjectsApi):
    async def read_projects_api_v1_projects__get(
        self, archived: bool | None = None, skip: int | None = None, limit: int | None = None
    ) -> list[m.Project]:
        """
        Read Projects
        """
        return await self._build_for_read_projects_api_v1_projects__get(archived=archived, skip=skip, limit=limit)

    async def create_project_api_v1_projects__post(self, body: m.ProjectCreate) -> m.Project:
        """
        Create Project
        """
        return await self._build_for_create_project_api_v1_projects__post(body=body)

    async def default_config_api_v1_projects_default_config_get(self) -> dict[str, Any]:
        """
        Default Config
        """
        return await self._build_for_default_config_api_v1_projects_default_config_get()

    async def read_project_api_v1_projects__id__get(self, id: int) -> m.Project:
        """
        Read Project
        """
        return await self._build_for_read_project_api_v1_projects__id__get(id=id)

    async def update_project_api_v1_projects__id__put(self, body: m.ProjectUpdate, id: int) -> m.Project:
        """
        Update Project
        """
        return await self._build_for_update_project_api_v1_projects__id__put(body=body, id=id)

    async def delete_project_api_v1_projects__id__delete(self, id: int) -> m.Project:
        """
        Delete Project
        """
        return await self._build_for_delete_project_api_v1_projects__id__delete(id=id)

    async def archive_project_api_v1_projects__id__archive_post(self, id: int) -> m.Project:
        """
        Archive Project
        """
        return await self._build_for_archive_project_api_v1_projects__id__archive_post(id=id)

    async def unarchive_project_api_v1_projects__id__unarchive_post(self, id: int) -> m.Project:
        """
        Unarchive Project
        """
        return await self._build_for_unarchive_project_api_v1_projects__id__unarchive_post(id=id)

    async def upload_pics_api_v1_projects__id__upload_pics_put(
        self, body: m.BodyUploadPicsApiV1ProjectsIdUploadPicsPut, id: int
    ) -> m.Project:
        """
        Upload Pics
        """
        return await self._build_for_upload_pics_api_v1_projects__id__upload_pics_put(body=body, id=id)

    async def remove_pics_cluster_type_api_v1_projects__id__pics_cluster_type_delete(
        self, id: int, cluster_name: str
    ) -> m.Project:
        """
        Remove Pics Cluster Type
        """
        return await self._build_for_remove_pics_cluster_type_api_v1_projects__id__pics_cluster_type_delete(
            id=id, cluster_name=cluster_name
        )

    async def applicable_test_cases_api_v1_projects__id__applicable_test_cases_get(
        self, id: int
    ) -> m.PICSApplicableTestCases:
        """
        Applicable Test Cases
        """
        return await self._build_for_applicable_test_cases_api_v1_projects__id__applicable_test_cases_get(id=id)

    async def export_project_config_api_v1_projects__id__export_get(self, id: int) -> m.ProjectCreate:
        """
        Export Project Config
        """
        return await self._build_for_export_project_config_api_v1_projects__id__export_get(id=id)

    async def importproject_config_api_v1_projects_import_post(
        self, body: m.BodyImportprojectConfigApiV1ProjectsImportPost
    ) -> m.Project:
        """
        Importproject Config
        """
        return await self._build_for_importproject_config_api_v1_projects_import_post(body=body)


class SyncProjectsApi(_ProjectsApi):
    def read_projects_api_v1_projects__get(
        self, archived: bool | None = None, skip: int | None = None, limit: int | None = None
    ) -> list[m.Project]:
        """
        Read Projects
        """
        coroutine = self._build_for_read_projects_api_v1_projects__get(archived=archived, skip=skip, limit=limit)
        return get_event_loop().run_until_complete(coroutine)

    def create_project_api_v1_projects__post(self, body: m.ProjectCreate) -> m.Project:
        """
        Create Project
        """
        coroutine = self._build_for_create_project_api_v1_projects__post(body=body)
        return get_event_loop().run_until_complete(coroutine)

    def default_config_api_v1_projects_default_config_get(self) -> dict[str, Any]:
        """
        Default Config
        """
        coroutine = self._build_for_default_config_api_v1_projects_default_config_get()
        return get_event_loop().run_until_complete(coroutine)

    def read_project_api_v1_projects__id__get(self, id: int) -> m.Project:
        """
        Read Project
        """
        coroutine = self._build_for_read_project_api_v1_projects__id__get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def update_project_api_v1_projects__id__put(self, body: m.ProjectUpdate, id: int) -> m.Project:
        """
        Update Project
        """
        coroutine = self._build_for_update_project_api_v1_projects__id__put(body=body, id=id)
        return get_event_loop().run_until_complete(coroutine)

    def delete_project_api_v1_projects__id__delete(self, id: int) -> m.Project:
        """
        Delete Project
        """
        coroutine = self._build_for_delete_project_api_v1_projects__id__delete(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def archive_project_api_v1_projects__id__archive_post(self, id: int) -> m.Project:
        """
        Archive Project
        """
        coroutine = self._build_for_archive_project_api_v1_projects__id__archive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def unarchive_project_api_v1_projects__id__unarchive_post(self, id: int) -> m.Project:
        """
        Unarchive Project
        """
        coroutine = self._build_for_unarchive_project_api_v1_projects__id__unarchive_post(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def upload_pics_api_v1_projects__id__upload_pics_put(
        self, body: m.BodyUploadPicsApiV1ProjectsIdUploadPicsPut, id: int
    ) -> m.Project:
        """
        Upload Pics
        """
        coroutine = self._build_for_upload_pics_api_v1_projects__id__upload_pics_put(body=body, id=id)
        return get_event_loop().run_until_complete(coroutine)

    def remove_pics_cluster_type_api_v1_projects__id__pics_cluster_type_delete(
        self, id: int, cluster_name: str
    ) -> m.Project:
        """
        Remove Pics Cluster Type
        """
        coroutine = self._build_for_remove_pics_cluster_type_api_v1_projects__id__pics_cluster_type_delete(
            id=id, cluster_name=cluster_name
        )
        return get_event_loop().run_until_complete(coroutine)

    def applicable_test_cases_api_v1_projects__id__applicable_test_cases_get(
        self, id: int
    ) -> m.PICSApplicableTestCases:
        """
        Applicable Test Cases
        """
        coroutine = self._build_for_applicable_test_cases_api_v1_projects__id__applicable_test_cases_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def export_project_config_api_v1_projects__id__export_get(self, id: int) -> m.ProjectCreate:
        """
        Export Project Config
        """
        coroutine = self._build_for_export_project_config_api_v1_projects__id__export_get(id=id)
        return get_event_loop().run_until_complete(coroutine)

    def importproject_config_api_v1_projects_import_post(
        self, body: m.BodyImportprojectConfigApiV1ProjectsImportPost
    ) -> m.Project:
        """
        Importproject Config
        """
        coroutine = self._build_for_importproject_config_api_v1_projects_import_post(body=body)
        return get_event_loop().run_until_complete(coroutine)
