#
# Copyright (c) 2023 Project CHIP Authors
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
from enum import Enum, IntEnum
from typing import Union

from pydantic import BaseModel

from th_cli.shared_constants import MessageTypeEnum

MESSAGE_EVENT_KEY = "message_event"
RESPONSE_KEY = "response"
STATUS_CODE_KEY = "status_code"




class TestStateEnum(str, Enum):
    __test__ = False  # Needed to indicate to PyTest that this is not a "test"
    PENDING = "pending"
    EXECUTING = "executing"
    PENDING_ACTUATION = "pending_actuation"  # TODO: Do we need this
    PASSED = "passed"  # Test Passed with no issued
    FAILED = "failed"  # Test Failed
    ERROR = "error"  # Test Error due to tool setup or environment
    NOT_APPLICABLE = "not_applicable"  # TODO: Do we need this for full cert runs?
    CANCELLED = "cancelled"


class UserResponseStatusEnum(IntEnum):
    OKAY = 0
    CANCELLED = -1
    TIMEOUT = -2
    INVALID = -3


class TestUpdateBase(BaseModel):
    state: TestStateEnum
    errors: list[str] | None
    failures: list[str] | None


class TestRunUpdate(TestUpdateBase):
    test_run_execution_id: int


class TestSuiteUpdate(TestUpdateBase):
    test_suite_execution_index: int


class TestCaseUpdate(TestSuiteUpdate):
    test_case_execution_index: int


class TestStepUpdate(TestCaseUpdate):
    test_step_execution_index: int


class TestUpdate(BaseModel):
    test_type: str
    body: Union[TestStepUpdate, TestCaseUpdate, TestSuiteUpdate, TestRunUpdate]


class TimeOutNotification(BaseModel):
    message_id: int


class TestLogRecord(BaseModel):
    level: str
    timestamp: str
    message: str
    test_suite_execution_id: int | None
    test_case_execution_id: int | None


class PromptRequest(BaseModel):
    prompt: str
    timeout: int
    message_id: int


class OptionsSelectPromptRequest(PromptRequest):
    options: dict[str, int]


class TextInputPromptRequest(PromptRequest):
    placeholder_text: str | None
    default_value: str | None
    regex_pattern: str | None


class StreamVerificationPromptRequest(OptionsSelectPromptRequest):
    pass


class PromptResponse(BaseModel):
    response: Union[int, str]
    status_code: UserResponseStatusEnum
    message_id: int


class SocketMessage(BaseModel):
    type: MessageTypeEnum
    payload: Union[
        OptionsSelectPromptRequest,
        TextInputPromptRequest,
        StreamVerificationPromptRequest,
        PromptRequest,
        PromptResponse,
        TestUpdate,
        TimeOutNotification,
        list[TestLogRecord],
    ]
