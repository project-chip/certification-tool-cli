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
from typing import Any

from httpx import Response


class ApiException(Exception):
    """Base exception for API client errors."""

    pass


class ResponseHandlingException(ApiException):
    """Exception raised when response handling fails."""

    def __init__(self, error: Exception):
        self.error = error
        super().__init__(f"Error handling response: {error}")


class UnexpectedResponse(ApiException):
    """Exception raised when response status is unexpected."""

    def __init__(self, status_code: int, content: Any):
        self.status_code = status_code
        self.content = content
        super().__init__(f"Unexpected response status: {status_code}")

    @classmethod
    def for_response(cls, response: Response) -> "UnexpectedResponse":
        """Create exception from httpx Response."""
        try:
            content = response.json()
        except Exception:
            content = response.text
        return cls(response.status_code, content)
