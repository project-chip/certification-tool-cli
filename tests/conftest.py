#
# Copyright (c) 2025 Project CHIP Authors
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
"""Shared test fixtures and configuration for th_cli tests."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from click.testing import CliRunner
from faker import Faker

from httpx import Headers

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.api_client import ApiClient, AsyncApis, SyncApis
from th_cli.api_lib_autogen.exceptions import UnexpectedResponse

# Initialize faker instance for generating test data
fake = Faker()


@pytest.fixture(scope="function", autouse=True)
def event_loop():
    """Create and set an event loop for each test.
    This is necessary for asyncio tests.
    """
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up
    loop.close()
    asyncio.set_event_loop(None)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config(temp_dir: Path) -> Path:
    """Provide a mock project configuration."""
    config_data = generate_test_project_data()
    config_file = temp_dir / "project_config.json"
    config_file.write_text(json.dumps(config_data, indent=2))
    return config_file


@pytest.fixture
def mock_project_config(temp_dir: Path) -> Path:
    """Provide a mock project configuration."""
    project_config_data = generate_test_project_data()["config"]
    config_file = temp_dir / "project_config.json"
    config_file.write_text(json.dumps(project_config_data, indent=2))
    return config_file


@pytest.fixture
def mock_properties_file(temp_dir: Path) -> Path:
    """Create a mock properties file for testing."""
    properties_content = """
[dut_config]
pairing_mode=ble-wifi
setup_code=20202021
discriminator=3840
chip_use_paa_certs=false
trace_log=false

[network]
ssid=TestNetwork
password=TestPassword123

[test_parameters]
custom_param=test_value
"""
    props_file = temp_dir / "test.properties"
    props_file.write_text(properties_content.strip())
    return props_file


@pytest.fixture
def mock_pics_dir(temp_dir: Path) -> Path:
    """Create a mock PICS configuration directory."""
    pics_dir = temp_dir / "pics"
    pics_dir.mkdir()

    pics_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<cluster>
    <name>TestCluster</name>
    <usage>
        <picsItem>
            <itemNumber>TC.TEST.1.1</itemNumber>
            <support>true</support>
        </picsItem>
    </usage>
    <clusterSide type="Server">
        <attributes>
            <picsItem>
                <itemNumber>TC.TEST.A.1</itemNumber>
                <support>true</support>
            </picsItem>
        </attributes>
        <events>
            <picsItem>
                <itemNumber>TC.TEST.E.1</itemNumber>
                <support>false</support>
            </picsItem>
        </events>
    </clusterSide>
</cluster>"""

    (pics_dir / "test_cluster.xml").write_text(pics_xml_content)
    return pics_dir


@pytest.fixture
def mock_api_client() -> Mock:
    """Create a mock API client."""
    mock_client = Mock(spec=ApiClient)
    mock_client.close = Mock()
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def mock_sync_apis(mock_api_client: Mock) -> Mock:
    """Create mock synchronous APIs."""
    mock_apis = Mock(spec=SyncApis)
    mock_apis.projects_api = Mock()
    mock_apis.test_collections_api = Mock()
    mock_apis.test_run_executions_api = Mock()
    mock_apis.versions_api = Mock()
    return mock_apis


@pytest.fixture
def mock_async_apis(mock_api_client: Mock) -> Mock:
    """Create mock asynchronous APIs."""
    mock_apis = Mock(spec=AsyncApis)
    mock_apis.projects_api = AsyncMock()
    mock_apis.test_collections_api = AsyncMock()
    mock_apis.test_run_executions_api = AsyncMock()
    mock_apis.versions_api = AsyncMock()
    return mock_apis


@pytest.fixture
def sample_project() -> api_models.Project:
    """Create a sample project for testing."""
    return api_models.Project(
        id=1,
        name="Test Project",
        config=api_models.TestEnvironmentConfig(
            network=api_models.NetworkConfig(
                wifi=api_models.WiFiConfig(
                    ssid="TestWiFi",
                    password="testpassword"
                ),
                thread=api_models.ThreadExternalConfig(
                    operational_dataset_hex="0e080000000000010000000300001235060004001fffe0020811111111222222220708fd"
                )
            ),
            dut_config=api_models.DutConfig(
                pairing_mode=api_models.DutPairingModeEnum.BLE_WIFI,
                setup_code="20202021",
                discriminator="3840",
                trace_log=False
            )
        ),
        created_at=fake.date_time(),
        updated_at=fake.date_time()
    )


@pytest.fixture
def sample_projects() -> list[api_models.Project]:
    """Create a list of sample projects for testing."""
    return [
        api_models.Project(
            id=i,
            name=f"Test Project {i}",
            config=api_models.TestEnvironmentConfig(
                network=api_models.NetworkConfig(
                    wifi=api_models.WiFiConfig(ssid="test", password="test"),
                    thread=api_models.ThreadExternalConfig(operational_dataset_hex="test")
                ),
                dut_config=api_models.DutConfig(
                    pairing_mode=api_models.DutPairingModeEnum.BLE_WIFI,
                    setup_code="20202021",
                    discriminator="3840",
                    trace_log=False
                )
            ),
            created_at=fake.date_time(),
            updated_at=fake.date_time()
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def sample_test_collections() -> api_models.TestCollections:
    """Create sample test collections for testing."""
    return api_models.TestCollections(
        test_collections={
            "SDK YAML Tests": api_models.TestCollection(
                name="SDK YAML Tests",
                path="/path/to/tests",
                test_suites={
                    "FirstChipToolSuite": api_models.TestSuite(
                        metadata=api_models.TestMetadata(
                            public_id="FirstChipToolSuite",
                            version="1.0",
                            title="First Chip Tool Suite",
                            description="Test suite for chip tool testing"
                        ),
                        test_cases={
                            "TC-ACE-1.1": api_models.TestCase(
                                metadata=api_models.TestMetadata(
                                    public_id="TC-ACE-1.1",
                                    version="1.0",
                                    title="Test Case ACE 1.1",
                                    description="Access Control Entry test"
                                )
                            ),
                            "TC-ACE-1.2": api_models.TestCase(
                                metadata=api_models.TestMetadata(
                                    public_id="TC-ACE-1.2",
                                    version="1.0",
                                    title="Test Case ACE 1.2",
                                    description="Access Control Entry test 2"
                                )
                            )
                        }
                    )
                }
            ),
            "SDK Python Tests": api_models.TestCollection(
                name="SDK Python Tests",
                path="/path/to/python/tests",
                test_suites={
                    "Python Testing Suite": api_models.TestSuite(
                        metadata=api_models.TestMetadata(
                            public_id="Python Testing Suite",
                            version="1.0",
                            title="Python Testing Suite",
                            description="Python test suite"
                        ),
                        test_cases={
                            "TC_ACE_1_3": api_models.TestCase(
                                metadata=api_models.TestMetadata(
                                    public_id="TC_ACE_1_3",
                                    version="1.0",
                                    title="Test Case ACE 1.3",
                                    description="Access Control Entry test 3"
                                )
                            )
                        }
                    )
                }
            )
        }
    )


@pytest.fixture
def sample_test_run_execution() -> api_models.TestRunExecutionWithChildren:
    """Create a sample test run execution for testing."""
    return api_models.TestRunExecutionWithChildren(
        id=1,
        title="Test Run 1",
        state=api_models.TestStateEnum.PENDING,
        project_id=1,
        test_suite_executions=[
            api_models.TestSuiteExecution(
                id=1,
                public_id="FirstChipToolSuite",
                state=api_models.TestStateEnum.PENDING,
                test_run_execution_id=1,
                test_suite_metadata_id=1,
                test_case_executions=[
                    api_models.TestCaseExecution(
                        id=1,
                        public_id="TC-ACE-1.1",
                        state=api_models.TestStateEnum.PENDING,
                        test_suite_execution_id=1,
                        test_case_metadata_id=1,
                        test_case_metadata=api_models.TestCaseMetadata(
                            id=1,
                            public_id="TC-ACE-1.1",
                            title="Test Case ACE 1.1",
                            description="Access Control Entry test",
                            version="1.0",
                            source_hash="abc123"
                        ),
                        test_step_executions=[]
                    )
                ],
                test_suite_metadata=api_models.TestSuiteMetadata(
                    id=1,
                    public_id="FirstChipToolSuite",
                    title="First Chip Tool Suite",
                    description="Test suite for chip tool testing",
                    version="1.0",
                    source_hash="def456"
                )
            )
        ]
    )


@pytest.fixture
def sample_test_runner_status() -> api_models.TestRunnerStatus:
    """Create a sample test runner status for testing."""
    return api_models.TestRunnerStatus(
        state=api_models.TestRunnerState.IDLE,
        test_run_execution_id=None
    )


@pytest.fixture
def mock_unexpected_response() -> UnexpectedResponse:
    """Create a mock UnexpectedResponse exception."""
    return UnexpectedResponse(
        status_code=404,
        reason_phrase="Not Found",
        content=b"Not Found",
        headers=Headers()
    )


@pytest.fixture
def mock_versions_info() -> dict[str, Any]:
    """Create mock versions information."""
    return {
        "backend_version": "1.0.0",
        "backend_sha": "abc123def",
        "test_harness_version": "2.0.0",
        "test_harness_sha": "def456ghi"
    }


@pytest.fixture(autouse=True)
def disable_colors():
    """Automatically disable colors for all tests to ensure consistent output."""
    # Set environment variable to disable colors
    os.environ["TH_CLI_NO_COLOR"] = "1"

    # Import and set colors disabled programmatically as well
    from th_cli.colorize import set_colors_enabled
    set_colors_enabled(False)

    yield

    # Cleanup
    if "TH_CLI_NO_COLOR" in os.environ:
        del os.environ["TH_CLI_NO_COLOR"]


class MockResponse:
    """Mock response class for API calls."""

    def __init__(self, data: Any, status_code: int = 200):
        self.data = data
        self.status_code = status_code

    def get(self, key: str, default: Any = None) -> Any:
        """Get method for dict-like access."""
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        return default

    def dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        if hasattr(self.data, 'dict'):
            return self.data.dict()
        return self.data if isinstance(self.data, dict) else {}


def create_mock_api_response(data: Any, status_code: int = 200) -> MockResponse:
    """Helper function to create mock API responses."""
    return MockResponse(data, status_code)


# Test data generators using Faker
def generate_test_project_data(**overrides) -> dict[str, Any]:
    """Generate test project data with optional overrides."""
    data = {
        "name": fake.company(),
        "config": {
            "network": {
                "wifi": {
                    "ssid": fake.name(),
                    "password": fake.password()
                },
                "thread": {
                    "operational_dataset_hex": "test_hex_value"
                }
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": str(fake.random_int(min=0, max=4095)),
                "trace_log": False
            }
        }
    }
    data.update(overrides)
    return data


def generate_test_ids(count: int = 3) -> list[str]:
    """Generate a list of test case IDs."""
    return [f"TC-TEST-{i}.{fake.random_int(min=1, max=9)}" for i in range(1, count + 1)]
