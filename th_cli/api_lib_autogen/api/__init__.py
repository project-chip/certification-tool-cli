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
"""API endpoint classes."""

from th_cli.api_lib_autogen.api.devices_api import AsyncDevicesApi, SyncDevicesApi
from th_cli.api_lib_autogen.api.operators_api import AsyncOperatorsApi, SyncOperatorsApi
from th_cli.api_lib_autogen.api.projects_api import AsyncProjectsApi, SyncProjectsApi
from th_cli.api_lib_autogen.api.test_collections_api import AsyncTestCollectionsApi, SyncTestCollectionsApi
from th_cli.api_lib_autogen.api.test_run_configs_api import AsyncTestRunConfigsApi, SyncTestRunConfigsApi
from th_cli.api_lib_autogen.api.test_run_executions_api import AsyncTestRunExecutionsApi, SyncTestRunExecutionsApi
from th_cli.api_lib_autogen.api.utils_api import AsyncUtilsApi, SyncUtilsApi
from th_cli.api_lib_autogen.api.version_api import AsyncVersionApi, SyncVersionApi

__all__ = [
    "TestCollectionsApi",
    "AsyncTestCollectionsApi",
    "SyncTestCollectionsApi",
    "ProjectsApi",
    "AsyncProjectsApi",
    "SyncProjectsApi",
    "OperatorsApi",
    "AsyncOperatorsApi",
    "SyncOperatorsApi",
    "TestRunExecutionsApi",
    "AsyncTestRunExecutionsApi",
    "SyncTestRunExecutionsApi",
    "TestRunConfigsApi",
    "AsyncTestRunConfigsApi",
    "SyncTestRunConfigsApi",
    "VersionApi",
    "AsyncVersionApi",
    "SyncVersionApi",
    "UtilsApi",
    "AsyncUtilsApi",
    "SyncUtilsApi",
    "DevicesApi",
    "AsyncDevicesApi",
    "SyncDevicesApi",
]
