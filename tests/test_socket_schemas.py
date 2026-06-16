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
"""Unit tests for th_cli/test_run/socket_schemas.py."""

import pytest
from pydantic import ValidationError

from th_cli.test_run.socket_schemas import (
    ImageVerificationPromptRequest,
    MessagePromptRequest,
    OptionsSelectPromptRequest,
    PromptRequest,
    PromptResponse,
    PushAVStreamVerificationRequest,
    SocketMessage,
    StreamVerificationPromptRequest,
    TestCaseUpdate,
    TestLogRecord,
    TestRunUpdate,
    TestStepUpdate,
    TestSuiteUpdate,
    TestUpdate,
    TextInputPromptRequest,
    TimeOutNotification,
    TwoWayTalkVerificationRequest,
    UserResponseStatusEnum,
)
# socket_schemas uses shared_constants.TestStateEnum (uppercase str enum: PASSED, FAILED …)
# and shared_constants.MessageTypeEnum
from th_cli.shared_constants import MessageTypeEnum, TestStateEnum


# ---------------------------------------------------------------------------
# UserResponseStatusEnum
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUserResponseStatusEnum:
    def test_okay_is_zero(self):
        assert UserResponseStatusEnum.OKAY == 0

    def test_cancelled_is_minus_one(self):
        assert UserResponseStatusEnum.CANCELLED == -1

    def test_timeout_is_minus_two(self):
        assert UserResponseStatusEnum.TIMEOUT == -2

    def test_invalid_is_minus_three(self):
        assert UserResponseStatusEnum.INVALID == -3

    def test_all_values_are_int(self):
        for member in UserResponseStatusEnum:
            assert isinstance(member.value, int)


# ---------------------------------------------------------------------------
# TestRunUpdate
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTestRunUpdate:
    def test_valid_construction(self):
        obj = TestRunUpdate(state=TestStateEnum.PASSED, test_run_execution_id=1)
        assert obj.state == TestStateEnum.PASSED
        assert obj.test_run_execution_id == 1

    def test_optional_errors_none_by_default(self):
        obj = TestRunUpdate(state=TestStateEnum.FAILED, test_run_execution_id=2)
        assert obj.errors is None

    def test_with_errors_and_failures(self):
        obj = TestRunUpdate(
            state=TestStateEnum.ERROR,
            test_run_execution_id=3,
            errors=["err1"],
            failures=["fail1"],
        )
        assert obj.errors == ["err1"]
        assert obj.failures == ["fail1"]


# ---------------------------------------------------------------------------
# TestSuiteUpdate
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTestSuiteUpdate:
    def test_valid_construction(self):
        obj = TestSuiteUpdate(state=TestStateEnum.EXECUTING, test_suite_execution_index=0)
        assert obj.test_suite_execution_index == 0

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            TestSuiteUpdate(state=TestStateEnum.PASSED)


# ---------------------------------------------------------------------------
# TestCaseUpdate
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTestCaseUpdate:
    def test_valid_construction(self):
        obj = TestCaseUpdate(
            state=TestStateEnum.PASSED,
            test_suite_execution_index=1,
            test_case_execution_index=2,
        )
        assert obj.test_case_execution_index == 2
        assert obj.test_suite_execution_index == 1


# ---------------------------------------------------------------------------
# TestStepUpdate
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTestStepUpdate:
    def test_valid_construction(self):
        obj = TestStepUpdate(
            state=TestStateEnum.PENDING,
            test_suite_execution_index=0,
            test_case_execution_index=1,
            test_step_execution_index=2,
        )
        assert obj.test_step_execution_index == 2

    def test_inherits_from_test_case_update(self):
        obj = TestStepUpdate(
            state=TestStateEnum.PASSED,
            test_suite_execution_index=0,
            test_case_execution_index=0,
            test_step_execution_index=0,
        )
        assert isinstance(obj, TestCaseUpdate)


# ---------------------------------------------------------------------------
# TestUpdate
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTestUpdate:
    def test_with_run_update_body(self):
        body = TestRunUpdate(state=TestStateEnum.PASSED, test_run_execution_id=1)
        obj = TestUpdate(test_type="test_run", body=body)
        assert obj.test_type == "test_run"

    def test_with_suite_update_body(self):
        body = TestSuiteUpdate(state=TestStateEnum.EXECUTING, test_suite_execution_index=0)
        obj = TestUpdate(test_type="test_suite", body=body)
        assert obj.test_type == "test_suite"

    def test_with_step_update_body(self):
        body = TestStepUpdate(
            state=TestStateEnum.PASSED,
            test_suite_execution_index=0,
            test_case_execution_index=0,
            test_step_execution_index=1,
        )
        obj = TestUpdate(test_type="test_step", body=body)
        assert isinstance(obj.body, TestStepUpdate)


# ---------------------------------------------------------------------------
# TimeOutNotification
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTimeOutNotification:
    def test_valid_construction(self):
        obj = TimeOutNotification(message_id=99)
        assert obj.message_id == 99

    def test_missing_message_id_raises(self):
        with pytest.raises(ValidationError):
            TimeOutNotification()


# ---------------------------------------------------------------------------
# TestLogRecord
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTestLogRecord:
    def test_minimal_construction(self):
        obj = TestLogRecord(level="INFO", timestamp=1234567890.0, message="hello")
        assert obj.level == "INFO"
        assert obj.message == "hello"

    def test_optional_index_fields_default_none(self):
        obj = TestLogRecord(level="WARNING", timestamp="2025-01-01T00:00:00", message="warn")
        assert obj.test_suite_execution_index is None
        assert obj.test_case_execution_index is None
        assert obj.test_step_execution_index is None

    def test_with_all_fields(self):
        obj = TestLogRecord(
            level="ERROR",
            timestamp=0.0,
            message="err",
            test_suite_execution_index=1,
            test_case_execution_index=2,
            test_step_execution_index=3,
        )
        assert obj.test_suite_execution_index == 1
        assert obj.test_case_execution_index == 2
        assert obj.test_step_execution_index == 3

    def test_timestamp_can_be_string(self):
        obj = TestLogRecord(level="INFO", timestamp="2025-06-01T12:00:00", message="msg")
        assert obj.timestamp == "2025-06-01T12:00:00"


# ---------------------------------------------------------------------------
# PromptRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPromptRequest:
    def test_valid_construction(self):
        obj = PromptRequest(prompt="Do something", timeout=30, message_id=1)
        assert obj.prompt == "Do something"
        assert obj.timeout == 30
        assert obj.message_id == 1


# ---------------------------------------------------------------------------
# OptionsSelectPromptRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestOptionsSelectPromptRequest:
    def test_valid_construction(self):
        obj = OptionsSelectPromptRequest(
            prompt="Select one",
            timeout=60,
            message_id=2,
            options={"PASS": 1, "FAIL": 2},
        )
        assert obj.options == {"PASS": 1, "FAIL": 2}


# ---------------------------------------------------------------------------
# TextInputPromptRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTextInputPromptRequest:
    def test_optional_fields_default_none(self):
        obj = TextInputPromptRequest(prompt="Enter text", timeout=30, message_id=3)
        assert obj.placeholder_text is None
        assert obj.default_value is None
        assert obj.regex_pattern is None

    def test_with_optional_fields(self):
        obj = TextInputPromptRequest(
            prompt="Enter text",
            timeout=30,
            message_id=3,
            placeholder_text="Type here",
            default_value="default",
            regex_pattern=r"\d+",
        )
        assert obj.placeholder_text == "Type here"
        assert obj.default_value == "default"
        assert obj.regex_pattern == r"\d+"


# ---------------------------------------------------------------------------
# MessagePromptRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMessagePromptRequest:
    def test_valid_construction(self):
        obj = MessagePromptRequest(prompt="Acknowledge this", timeout=30, message_id=4)
        assert isinstance(obj, PromptRequest)


# ---------------------------------------------------------------------------
# StreamVerificationPromptRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStreamVerificationPromptRequest:
    def test_is_options_select(self):
        obj = StreamVerificationPromptRequest(
            prompt="Verify stream",
            timeout=30,
            message_id=5,
            options={"OK": 1},
        )
        assert isinstance(obj, OptionsSelectPromptRequest)


# ---------------------------------------------------------------------------
# ImageVerificationPromptRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImageVerificationPromptRequest:
    def test_includes_image_hex_str(self):
        obj = ImageVerificationPromptRequest(
            prompt="Verify image",
            timeout=30,
            message_id=6,
            options={"PASS": 1},
            image_hex_str="ffd8ffe0",
        )
        assert obj.image_hex_str == "ffd8ffe0"

    def test_missing_image_hex_str_raises(self):
        with pytest.raises(ValidationError):
            ImageVerificationPromptRequest(
                prompt="Verify image",
                timeout=30,
                message_id=6,
                options={"PASS": 1},
            )


# ---------------------------------------------------------------------------
# TwoWayTalkVerificationRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoWayTalkVerificationRequest:
    def test_is_options_select(self):
        obj = TwoWayTalkVerificationRequest(
            prompt="Verify talk",
            timeout=30,
            message_id=7,
            options={"PASS": 1, "FAIL": 2},
        )
        assert isinstance(obj, OptionsSelectPromptRequest)


# ---------------------------------------------------------------------------
# PushAVStreamVerificationRequest
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPushAVStreamVerificationRequest:
    def test_is_options_select(self):
        obj = PushAVStreamVerificationRequest(
            prompt="Verify AV",
            timeout=30,
            message_id=8,
            options={"PASS": 1},
        )
        assert isinstance(obj, OptionsSelectPromptRequest)


# ---------------------------------------------------------------------------
# PromptResponse
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPromptResponse:
    def test_integer_response(self):
        obj = PromptResponse(response=1, status_code=UserResponseStatusEnum.OKAY, message_id=1)
        assert obj.response == 1

    def test_string_response(self):
        obj = PromptResponse(response="some text", status_code=UserResponseStatusEnum.OKAY, message_id=2)
        assert obj.response == "some text"

    def test_cancelled_status(self):
        obj = PromptResponse(response=0, status_code=UserResponseStatusEnum.CANCELLED, message_id=3)
        assert obj.status_code == UserResponseStatusEnum.CANCELLED

    def test_timeout_status(self):
        obj = PromptResponse(response=0, status_code=UserResponseStatusEnum.TIMEOUT, message_id=4)
        assert obj.status_code == UserResponseStatusEnum.TIMEOUT


# ---------------------------------------------------------------------------
# SocketMessage
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSocketMessage:
    def test_with_prompt_response_payload(self):
        payload = PromptResponse(
            response=1,
            status_code=UserResponseStatusEnum.OKAY,
            message_id=1,
        )
        msg = SocketMessage(type=MessageTypeEnum.PROMPT_RESPONSE, payload=payload)
        assert msg.type == MessageTypeEnum.PROMPT_RESPONSE

    def test_with_test_log_list_payload(self):
        logs = [TestLogRecord(level="INFO", timestamp=0.0, message="hello")]
        msg = SocketMessage(type=MessageTypeEnum.TEST_LOG_RECORDS, payload=logs)
        assert isinstance(msg.payload, list)

    def test_with_test_update_payload(self):
        body = TestRunUpdate(state=TestStateEnum.PASSED, test_run_execution_id=1)
        update = TestUpdate(test_type="test_run", body=body)
        msg = SocketMessage(type=MessageTypeEnum.TEST_UPDATE, payload=update)
        assert isinstance(msg.payload, TestUpdate)
