
# flake8: noqa E501
from asyncio import get_event_loop
from typing import TYPE_CHECKING, Awaitable

from th_cli.api_lib_autogen import models as m

if TYPE_CHECKING:
    from th_cli.api_lib_autogen.api_client import ApiClient


class _VersionApi:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def _build_for_get_test_harness_backend_version_api_v1_version_get(self) -> Awaitable[m.TestHarnessBackendVersion]:
        """
        Retrieve version of the Test Engine.
        """
        return self.api_client.request(
            type_=m.TestHarnessBackendVersion,
            method="GET",
            url="/api/v1/version",
            
            
            
            
            
            
        )


class AsyncVersionApi(_VersionApi):
    async def get_test_harness_backend_version_api_v1_version_get(self) -> m.TestHarnessBackendVersion:
        """
        Retrieve version of the Test Engine.
        """
        return await self._build_for_get_test_harness_backend_version_api_v1_version_get()


class SyncVersionApi(_VersionApi):
    def get_test_harness_backend_version_api_v1_version_get(self) -> m.TestHarnessBackendVersion:
        """
        Retrieve version of the Test Engine.
        """
        coroutine = self._build_for_get_test_harness_backend_version_api_v1_version_get()
        return get_event_loop().run_until_complete(coroutine)
