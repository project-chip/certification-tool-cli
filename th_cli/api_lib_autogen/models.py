from datetime import datetime
from enum import Enum
from typing import Any  # noqa
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost(BaseModel):
    test_run_execution_in: "TestRunExecutionCreate" = Field(..., alias="test_run_execution_in")
    selected_tests: "Dict[str, Dict[str, Dict[str, int]]]" = Field(..., alias="selected_tests")
    config: "Optional[Any]" = Field(None, alias="config")
    execution_config: "Optional[Any]" = Field(None, alias="execution_config")
    pics: "Optional[Any]" = Field(None, alias="pics")


class BodyCreateTestRunExecutionApiV1TestRunExecutionsPost(BaseModel):
    test_run_execution_in: "TestRunExecutionCreate" = Field(..., alias="test_run_execution_in")
    selected_tests: "Dict[str, Dict[str, Dict[str, int]]]" = Field(..., alias="selected_tests")


class ChipServerInfo(BaseModel):
    node_id: "int" = Field(..., alias="node_id")
    node_id_hex: "str" = Field(..., alias="node_id_hex")
    manual_pairing_code: "Optional[str]" = Field(None, alias="manual_pairing_code")


class ExportedTestRunExecution(BaseModel):
    db_revision: "str" = Field(..., alias="db_revision")
    test_run_execution: "TestRunExecutionToExport" = Field(..., alias="test_run_execution")


class HTTPValidationError(BaseModel):
    detail: "Optional[List[ValidationError]]" = Field(None, alias="detail")


class LocationInner(BaseModel):
    pass


class Msg(BaseModel):
    msg: "str" = Field(..., alias="msg")


class Operator(BaseModel):
    name: "str" = Field(..., alias="name")
    id: "int" = Field(..., alias="id")


class OperatorCreate(BaseModel):
    name: "str" = Field(..., alias="name")


class OperatorToExport(BaseModel):
    name: "str" = Field(..., alias="name")


class OperatorUpdate(BaseModel):
    name: "Optional[str]" = Field(None, alias="name")


class PICS(BaseModel):
    clusters: "Optional[Dict[str, PICSCluster]]" = Field(None, alias="clusters")


class PICSApplicableTestCases(BaseModel):
    test_cases: "List[str]" = Field(..., alias="test_cases")


class PICSCluster(BaseModel):
    name: "str" = Field(..., alias="name")
    items: "Optional[Dict[str, PICSItem]]" = Field(None, alias="items")


class PICSItem(BaseModel):
    number: "str" = Field(..., alias="number")
    enabled: "bool" = Field(..., alias="enabled")


class Project(BaseModel):
    name: "str" = Field(..., alias="name")
    config: "Optional[Any]" = Field(None, alias="config")
    pics: "Any" = Field({}, alias="pics")
    id: "int" = Field(..., alias="id")
    created_at: "datetime" = Field(..., alias="created_at")
    updated_at: "datetime" = Field(..., alias="updated_at")
    archived_at: "Optional[datetime]" = Field(None, alias="archived_at")


class ProjectCreate(BaseModel):
    name: "str" = Field(..., alias="name")
    config: "Optional[Any]" = Field(None, alias="config")
    pics: "Any" = Field({}, alias="pics")


class ProjectUpdate(BaseModel):
    name: "Optional[str]" = Field(None, alias="name")
    config: "Optional[Any]" = Field(None, alias="config")
    pics: "Optional[PICS]" = Field(None, alias="pics")


class ResponseDefaultConfigApiV1ProjectsDefaultConfigGet(BaseModel):
    test_parameters: "Optional[Any]" = Field(None, alias="test_parameters")


class TestCase(BaseModel):
    metadata: "TestMetadata" = Field(..., alias="metadata")


class TestCaseExecution(BaseModel):
    state: "TestStateEnum" = Field(..., alias="state")
    public_id: "str" = Field(..., alias="public_id")
    execution_index: "int" = Field(..., alias="execution_index")
    id: "int" = Field(..., alias="id")
    test_suite_execution_id: "int" = Field(..., alias="test_suite_execution_id")
    test_case_metadata_id: "int" = Field(..., alias="test_case_metadata_id")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    errors: "Optional[List[str]]" = Field(None, alias="errors")
    test_case_metadata: "TestCaseMetadata" = Field(..., alias="test_case_metadata")
    test_step_executions: "List[TestStepExecution]" = Field(..., alias="test_step_executions")


class TestCaseExecutionToExport(BaseModel):
    state: "TestStateEnum" = Field(..., alias="state")
    public_id: "str" = Field(..., alias="public_id")
    execution_index: "int" = Field(..., alias="execution_index")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    errors: "Optional[List[str]]" = Field(None, alias="errors")
    test_case_metadata: "TestCaseMetadataBase" = Field(..., alias="test_case_metadata")
    test_step_executions: "List[TestStepExecutionToExport]" = Field(..., alias="test_step_executions")
    created_at: "datetime" = Field(..., alias="created_at")


class TestCaseMetadata(BaseModel):
    public_id: "str" = Field(..., alias="public_id")
    title: "str" = Field(..., alias="title")
    description: "str" = Field(..., alias="description")
    version: "str" = Field(..., alias="version")
    source_hash: "str" = Field(..., alias="source_hash")
    mandatory: "bool" = Field(False, alias="mandatory")
    id: "int" = Field(..., alias="id")


class TestCaseMetadataBase(BaseModel):
    public_id: "str" = Field(..., alias="public_id")
    title: "str" = Field(..., alias="title")
    description: "str" = Field(..., alias="description")
    version: "str" = Field(..., alias="version")
    source_hash: "str" = Field(..., alias="source_hash")
    mandatory: "bool" = Field(False, alias="mandatory")


class TestCollection(BaseModel):
    name: "str" = Field(..., alias="name")
    path: "str" = Field(..., alias="path")
    test_suites: "Dict[str, TestSuite]" = Field(..., alias="test_suites")


class TestCollections(BaseModel):
    test_collections: "Dict[str, TestCollection]" = Field(..., alias="test_collections")


class TestEnvironmentConfig(BaseModel):
    test_parameters: "Optional[Any]" = Field(None, alias="test_parameters")


class TestHarnessBackendVersion(BaseModel):
    version: "str" = Field(..., alias="version")
    sha: "str" = Field(..., alias="sha")
    sdk_sha: "str" = Field(..., alias="sdk_sha")
    sdk_docker_tag: "str" = Field(..., alias="sdk_docker_tag")
    db_revision: "str" = Field(..., alias="db_revision")


class TestMetadata(BaseModel):
    public_id: "str" = Field(..., alias="public_id")
    version: "str" = Field(..., alias="version")
    title: "str" = Field(..., alias="title")
    description: "str" = Field(..., alias="description")
    mandatory: "bool" = Field(False, alias="mandatory")


class TestRunConfig(BaseModel):
    name: "str" = Field(..., alias="name")
    dut_name: "str" = Field(..., alias="dut_name")
    selected_tests: "Optional[Dict[str, Dict[str, Dict[str, int]]]]" = Field(None, alias="selected_tests")
    id: "int" = Field(..., alias="id")


class TestRunConfigCreate(BaseModel):
    name: "str" = Field(..., alias="name")
    dut_name: "str" = Field(..., alias="dut_name")
    selected_tests: "Optional[Dict[str, Dict[str, Dict[str, int]]]]" = Field(None, alias="selected_tests")


class TestRunConfigToExport(BaseModel):
    name: "str" = Field(..., alias="name")
    dut_name: "str" = Field(..., alias="dut_name")
    selected_tests: "Optional[Dict[str, Dict[str, Dict[str, int]]]]" = Field(None, alias="selected_tests")
    created_at: "datetime" = Field(..., alias="created_at")


class TestRunConfigUpdate(BaseModel):
    name: "str" = Field(..., alias="name")


class TestRunExecution(BaseModel):
    title: "str" = Field(..., alias="title")
    description: "Optional[str]" = Field(None, alias="description")
    execution_config: "Optional[Any]" = Field(None, alias="execution_config")
    certification_mode: "bool" = Field(False, alias="certification_mode")
    test_run_config_id: "Optional[int]" = Field(None, alias="test_run_config_id")
    project_id: "Optional[int]" = Field(None, alias="project_id")
    id: "int" = Field(..., alias="id")
    state: "TestStateEnum" = Field(..., alias="state")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    imported_at: "Optional[datetime]" = Field(None, alias="imported_at")
    archived_at: "Optional[datetime]" = Field(None, alias="archived_at")
    operator: "Optional[Operator]" = Field(None, alias="operator")


class TestRunExecutionCreate(BaseModel):
    title: "str" = Field(..., alias="title")
    description: "Optional[str]" = Field(None, alias="description")
    execution_config: "Optional[Any]" = Field(None, alias="execution_config")
    certification_mode: "bool" = Field(False, alias="certification_mode")
    test_run_config_id: "Optional[int]" = Field(None, alias="test_run_config_id")
    project_id: "Optional[int]" = Field(None, alias="project_id")
    operator_id: "Optional[int]" = Field(None, alias="operator_id")


class TestRunExecutionInDBBase(BaseModel):
    title: "str" = Field(..., alias="title")
    description: "Optional[str]" = Field(None, alias="description")
    execution_config: "Optional[Any]" = Field(None, alias="execution_config")
    certification_mode: "bool" = Field(False, alias="certification_mode")
    test_run_config_id: "Optional[int]" = Field(None, alias="test_run_config_id")
    project_id: "Optional[int]" = Field(None, alias="project_id")
    id: "int" = Field(..., alias="id")
    state: "TestStateEnum" = Field(..., alias="state")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    imported_at: "Optional[datetime]" = Field(None, alias="imported_at")
    archived_at: "Optional[datetime]" = Field(None, alias="archived_at")


class TestRunExecutionStats(BaseModel):
    test_case_count: "int" = Field(0, alias="test_case_count")
    states: "Optional[Dict[str, int]]" = Field(None, alias="states")


class TestRunExecutionToExport(BaseModel):
    title: "str" = Field(..., alias="title")
    description: "Optional[str]" = Field(None, alias="description")
    execution_config: "Optional[Any]" = Field(None, alias="execution_config")
    certification_mode: "bool" = Field(False, alias="certification_mode")
    state: "TestStateEnum" = Field(..., alias="state")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    archived_at: "Optional[datetime]" = Field(None, alias="archived_at")
    test_suite_executions: "Optional[List[TestSuiteExecutionToExport]]" = Field(None, alias="test_suite_executions")
    created_at: "datetime" = Field(..., alias="created_at")
    log: "List[TestRunLogEntry]" = Field(..., alias="log")
    operator: "Optional[OperatorToExport]" = Field(None, alias="operator")
    test_run_config: "Optional[TestRunConfigToExport]" = Field(None, alias="test_run_config")


class TestRunExecutionWithChildren(BaseModel):
    title: "str" = Field(..., alias="title")
    description: "Optional[str]" = Field(None, alias="description")
    execution_config: "Optional[Any]" = Field(None, alias="execution_config")
    certification_mode: "bool" = Field(False, alias="certification_mode")
    test_run_config_id: "Optional[int]" = Field(None, alias="test_run_config_id")
    project_id: "Optional[int]" = Field(None, alias="project_id")
    id: "int" = Field(..., alias="id")
    state: "TestStateEnum" = Field(..., alias="state")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    imported_at: "Optional[datetime]" = Field(None, alias="imported_at")
    archived_at: "Optional[datetime]" = Field(None, alias="archived_at")
    operator: "Optional[Operator]" = Field(None, alias="operator")
    test_suite_executions: "Optional[List[TestSuiteExecution]]" = Field(None, alias="test_suite_executions")


class TestRunExecutionWithStats(BaseModel):
    title: "str" = Field(..., alias="title")
    description: "Optional[str]" = Field(None, alias="description")
    execution_config: "Optional[Any]" = Field(None, alias="execution_config")
    certification_mode: "bool" = Field(False, alias="certification_mode")
    test_run_config_id: "Optional[int]" = Field(None, alias="test_run_config_id")
    project_id: "Optional[int]" = Field(None, alias="project_id")
    id: "int" = Field(..., alias="id")
    state: "TestStateEnum" = Field(..., alias="state")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    imported_at: "Optional[datetime]" = Field(None, alias="imported_at")
    archived_at: "Optional[datetime]" = Field(None, alias="archived_at")
    operator: "Optional[Operator]" = Field(None, alias="operator")
    test_case_stats: "TestRunExecutionStats" = Field(..., alias="test_case_stats")


class TestRunLogEntry(BaseModel):
    level: "str" = Field(..., alias="level")
    timestamp: "float" = Field(..., alias="timestamp")
    message: "str" = Field(..., alias="message")
    test_suite_execution_index: "Optional[int]" = Field(None, alias="test_suite_execution_index")
    test_case_execution_index: "Optional[int]" = Field(None, alias="test_case_execution_index")
    test_step_execution_index: "Optional[int]" = Field(None, alias="test_step_execution_index")


class TestRunnerState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    RUNNING = "running"


class TestRunnerStatus(BaseModel):
    state: "TestRunnerState" = Field(..., alias="state")
    test_run_execution_id: "Optional[int]" = Field(None, alias="test_run_execution_id")


class TestStateEnum(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    PENDING_ACTUATION = "pending_actuation"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    NOT_APPLICABLE = "not_applicable"
    CANCELLED = "cancelled"


class TestStepExecution(BaseModel):
    state: "TestStateEnum" = Field(..., alias="state")
    title: "str" = Field(..., alias="title")
    execution_index: "int" = Field(..., alias="execution_index")
    id: "int" = Field(..., alias="id")
    test_case_execution_id: "int" = Field(..., alias="test_case_execution_id")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    errors: "Optional[List[str]]" = Field(None, alias="errors")
    failures: "Optional[List[str]]" = Field(None, alias="failures")


class TestStepExecutionToExport(BaseModel):
    state: "TestStateEnum" = Field(..., alias="state")
    title: "str" = Field(..., alias="title")
    execution_index: "int" = Field(..., alias="execution_index")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    errors: "Optional[List[str]]" = Field(None, alias="errors")
    failures: "Optional[List[str]]" = Field(None, alias="failures")
    created_at: "datetime" = Field(..., alias="created_at")


class TestSuite(BaseModel):
    metadata: "TestMetadata" = Field(..., alias="metadata")
    test_cases: "Dict[str, TestCase]" = Field(..., alias="test_cases")


class TestSuiteExecution(BaseModel):
    state: "TestStateEnum" = Field(..., alias="state")
    public_id: "str" = Field(..., alias="public_id")
    execution_index: "int" = Field(..., alias="execution_index")
    collection_id: "str" = Field(..., alias="collection_id")
    mandatory: "bool" = Field(False, alias="mandatory")
    id: "int" = Field(..., alias="id")
    test_run_execution_id: "int" = Field(..., alias="test_run_execution_id")
    test_suite_metadata_id: "int" = Field(..., alias="test_suite_metadata_id")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    errors: "Optional[List[str]]" = Field(None, alias="errors")
    test_case_executions: "List[TestCaseExecution]" = Field(..., alias="test_case_executions")
    test_suite_metadata: "TestSuiteMetadata" = Field(..., alias="test_suite_metadata")


class TestSuiteExecutionToExport(BaseModel):
    state: "TestStateEnum" = Field(..., alias="state")
    public_id: "str" = Field(..., alias="public_id")
    execution_index: "int" = Field(..., alias="execution_index")
    collection_id: "str" = Field(..., alias="collection_id")
    mandatory: "bool" = Field(False, alias="mandatory")
    started_at: "Optional[datetime]" = Field(None, alias="started_at")
    completed_at: "Optional[datetime]" = Field(None, alias="completed_at")
    errors: "Optional[List[str]]" = Field(None, alias="errors")
    test_case_executions: "List[TestCaseExecutionToExport]" = Field(..., alias="test_case_executions")
    test_suite_metadata: "TestSuiteMetadataBase" = Field(..., alias="test_suite_metadata")
    created_at: "datetime" = Field(..., alias="created_at")


class TestSuiteMetadata(BaseModel):
    public_id: "str" = Field(..., alias="public_id")
    title: "str" = Field(..., alias="title")
    description: "str" = Field(..., alias="description")
    version: "str" = Field(..., alias="version")
    source_hash: "str" = Field(..., alias="source_hash")
    mandatory: "bool" = Field(False, alias="mandatory")
    id: "int" = Field(..., alias="id")


class TestSuiteMetadataBase(BaseModel):
    public_id: "str" = Field(..., alias="public_id")
    title: "str" = Field(..., alias="title")
    description: "str" = Field(..., alias="description")
    version: "str" = Field(..., alias="version")
    source_hash: "str" = Field(..., alias="source_hash")
    mandatory: "bool" = Field(False, alias="mandatory")


class ValidationError(BaseModel):
    loc: "List[LocationInner]" = Field(..., alias="loc")
    msg: "str" = Field(..., alias="msg")
    type: "str" = Field(..., alias="type")
