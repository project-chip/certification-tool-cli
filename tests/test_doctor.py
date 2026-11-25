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
"""Tests for the doctor command."""

import importlib
import json
import socket
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from httpx import ConnectError, ConnectTimeout, ReadTimeout

from th_cli.api_lib_autogen import models as api_models
from th_cli.api_lib_autogen.exceptions import ResponseHandlingException, UnexpectedResponse
from th_cli.commands.doctor import CheckResult, Status, check_config, check_docker, classify_error, doctor
from th_cli.config import Config
from th_cli.exceptions import ConfigurationError

# th_cli.commands.doctor is shadowed by the command object in the package namespace
doctor_module = importlib.import_module("th_cli.commands.doctor")

VERSION = api_models.TestHarnessBackendVersion(
    version="2.16", sha="abcdef123456", sdk_sha="s", sdk_docker_tag="tag", db_revision="rev1"
)


def _wrapped(error: Exception) -> ResponseHandlingException:
    return ResponseHandlingException(error)


def _gaierror_connect_error() -> ConnectError:
    error = ConnectError("")
    error.__cause__ = socket.gaierror(-2, "Name or service not known")
    return error


def _refused_connect_error() -> ConnectError:
    error = ConnectError("")
    error.__cause__ = ConnectionRefusedError(111, "Connection refused")
    return error


@pytest.mark.unit
@pytest.mark.cli
class TestClassifyError:
    def test_http_status(self) -> None:
        assert classify_error(UnexpectedResponse(502, b"")) == "HTTP 502 from the backend"

    def test_connection_refused(self) -> None:
        assert classify_error(_wrapped(_refused_connect_error())) == "connection refused"

    def test_dns(self) -> None:
        assert classify_error(_wrapped(_gaierror_connect_error())).startswith("DNS lookup failed")

    @pytest.mark.parametrize("error", [ReadTimeout(""), ConnectTimeout("")])
    def test_timeout(self, error: Exception) -> None:
        assert classify_error(_wrapped(error)).startswith("timeout")

    def test_plain_connect_error_is_never_empty(self) -> None:
        assert classify_error(_wrapped(ConnectError(""))) == "cannot connect (ConnectError)"

    def test_unknown_error_uses_its_description(self) -> None:
        assert classify_error(_wrapped(ValueError("bad body"))) == "ValueError: bad body"


@pytest.mark.unit
@pytest.mark.cli
class TestCheckConfig:
    def test_valid_config(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text('{"hostname": "th.local"}')
        with (
            patch("th_cli.commands.doctor.get_config_search_paths", return_value=[tmp_path]),
            patch("th_cli.config.get_config_search_paths", return_value=[tmp_path]),
        ):
            result, config = check_config()
        assert result.status == Status.PASS
        assert config is not None and config.hostname == "th.local"
        assert str(tmp_path / "config.json") in result.detail

    def test_invalid_config_reported_not_raised(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text("{bad")
        with (
            patch("th_cli.commands.doctor.get_config_search_paths", return_value=[tmp_path]),
            patch("th_cli.config.get_config_search_paths", return_value=[tmp_path]),
        ):
            result, config = check_config()
        assert result.status == Status.FAIL
        assert config is None
        assert "config.json" in result.detail

    def test_defaults_used_is_a_warning_and_output_is_captured(self, tmp_path: Path, capsys) -> None:
        with (
            patch("th_cli.commands.doctor.get_config_search_paths", return_value=[tmp_path]),
            patch("th_cli.config.get_config_search_paths", return_value=[tmp_path]),
        ):
            result, config = check_config()
        assert result.status == Status.WARN
        assert config is not None and config.hostname == "localhost"
        assert "defaults" in result.detail
        assert capsys.readouterr().out == ""

    def test_broken_example_falls_back_with_warning(self, tmp_path: Path) -> None:
        (tmp_path / "config.json.example").write_text("{bad")
        with (
            patch("th_cli.commands.doctor.get_config_search_paths", return_value=[tmp_path]),
            patch("th_cli.config.get_config_search_paths", return_value=[tmp_path]),
        ):
            result, _ = check_config()
        assert result.status == Status.WARN
        assert "Could not load example config" in result.detail


@pytest.fixture
def backend(mock_api_client: Mock):
    """Patch get_client and SyncApis so each probe's response can be set per test."""
    apis = Mock()
    apis.version_api.get_test_harness_backend_version_api_v1_version_get.return_value = VERSION
    status = Mock()
    status.state = Mock(value="idle")
    apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get.return_value = status
    apis.projects_api.read_projects_api_v1_projects__get.return_value = []
    with (
        patch("th_cli.commands.doctor.get_client", return_value=mock_api_client),
        patch("th_cli.commands.doctor.SyncApis", return_value=apis),
    ):
        yield apis


@pytest.mark.unit
@pytest.mark.cli
class TestCheckBackend:
    def test_all_healthy(self, backend: Mock) -> None:
        results = doctor_module.check_backend()
        assert [r.status for r in results] == [Status.PASS] * 4
        assert "backend 2.16 (abcdef12)" in results[1].detail

    def test_unreachable_skips_the_rest_with_reason(self, backend: Mock) -> None:
        backend.version_api.get_test_harness_backend_version_api_v1_version_get.side_effect = _wrapped(
            _refused_connect_error()
        )
        results = doctor_module.check_backend()
        assert results[0].status == Status.FAIL
        assert results[0].detail == "connection refused"
        assert all(r.status == Status.SKIP for r in results[1:])

    def test_database_failure_is_a_warning(self, backend: Mock) -> None:
        backend.projects_api.read_projects_api_v1_projects__get.side_effect = UnexpectedResponse(500, b"")
        results = doctor_module.check_backend()
        assert results[0].status == Status.PASS
        assert results[-1].name == "database" and results[-1].status == Status.WARN
        assert "HTTP 500" in results[-1].detail

    def test_runner_status_failure_is_a_warning(self, backend: Mock) -> None:
        runner = backend.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get
        runner.side_effect = _wrapped(ReadTimeout(""))
        results = doctor_module.check_backend()
        assert results[2].status == Status.WARN

    def test_unexpected_exception_in_probe_is_reported(self, backend: Mock) -> None:
        backend.version_api.get_test_harness_backend_version_api_v1_version_get.side_effect = RuntimeError("boom")
        assert doctor_module.check_backend()[0].detail == "boom"

    def test_client_construction_failure(self) -> None:
        with patch("th_cli.commands.doctor.get_client", side_effect=ConfigurationError("no host")):
            results = doctor_module.check_backend()
        assert results[0].status == Status.FAIL and results[0].detail == "no host"


@pytest.mark.unit
@pytest.mark.cli
class TestCheckDocker:
    def test_skipped_without_docker(self) -> None:
        with patch("th_cli.commands.doctor.shutil.which", return_value=None):
            results = check_docker(0)
        assert [r.status for r in results] == [Status.SKIP]

    def test_states(self) -> None:
        def fake(args: list[str]) -> subprocess.CompletedProcess:
            name = args[-1]
            if name.endswith("backend-1"):
                return subprocess.CompletedProcess(args, 0, "running\n", "")
            if name.endswith("db-1"):
                return subprocess.CompletedProcess(args, 0, "exited\n", "")
            return subprocess.CompletedProcess(args, 1, "", "No such object")

        with (
            patch("th_cli.commands.doctor.shutil.which", return_value="/usr/bin/docker"),
            patch("th_cli.commands.doctor._run_docker", side_effect=fake),
        ):
            results = {r.name: r.status for r in check_docker(0)}
        assert results["certification-tool-backend-1"] == Status.PASS
        assert results["certification-tool-db-1"] == Status.FAIL
        assert results["certification-tool-proxy-1"] == Status.WARN

    def test_docker_failing_to_run_is_skipped(self) -> None:
        with (
            patch("th_cli.commands.doctor.shutil.which", return_value="/usr/bin/docker"),
            patch("th_cli.commands.doctor._run_docker", side_effect=subprocess.TimeoutExpired("docker", 10)),
        ):
            results = check_docker(0)
        assert [r.status for r in results] == [Status.SKIP]

    def test_log_tail_included_on_request(self) -> None:
        def fake(args: list[str]) -> subprocess.CompletedProcess:
            if args[0] == "logs":
                return subprocess.CompletedProcess(args, 0, "line1\n", "line2 password=x\n")
            return subprocess.CompletedProcess(args, 0, "running\n", "")

        with (
            patch("th_cli.commands.doctor.shutil.which", return_value="/usr/bin/docker"),
            patch("th_cli.commands.doctor._run_docker", side_effect=fake),
        ):
            results = check_docker(5)
        assert results[-1].name == "backend logs"
        assert "line2" in results[-1].data["log_tail"]

    def test_log_failure_is_a_warning(self) -> None:
        def fake(args: list[str]) -> subprocess.CompletedProcess:
            if args[0] == "logs":
                raise OSError("denied")
            return subprocess.CompletedProcess(args, 0, "running\n", "")

        with (
            patch("th_cli.commands.doctor.shutil.which", return_value="/usr/bin/docker"),
            patch("th_cli.commands.doctor._run_docker", side_effect=fake),
        ):
            assert check_docker(5)[-1].status == Status.WARN


@pytest.mark.unit
@pytest.mark.cli
class TestDoctorCommand:
    def _run(self, cli_runner: CliRunner, results: list[CheckResult], *args: str):
        with patch("th_cli.commands.doctor.run_checks", return_value=results) as run_checks:
            result = cli_runner.invoke(doctor, list(args))
        return result, run_checks

    def test_success_exit_zero(self, cli_runner: CliRunner) -> None:
        result, _ = self._run(cli_runner, [CheckResult("config", Status.PASS, "ok")])
        assert result.exit_code == 0
        assert "No problems found" in result.output

    def test_warning_does_not_fail(self, cli_runner: CliRunner) -> None:
        result, _ = self._run(cli_runner, [CheckResult("config", Status.WARN, "defaults")])
        assert result.exit_code == 0

    def test_failure_exit_nonzero(self, cli_runner: CliRunner) -> None:
        result, _ = self._run(cli_runner, [CheckResult("backend reachable", Status.FAIL, "connection refused")])
        assert result.exit_code == 1
        assert "connection refused" in result.output
        assert "1 check(s) failed" in result.output

    def test_json_output(self, cli_runner: CliRunner) -> None:
        results = [
            CheckResult("config", Status.PASS, "ok", {"hostname": "10.1.2.3", "wifi_password": "pw"}),
            CheckResult("backend reachable", Status.FAIL, "timeout"),
        ]
        result, _ = self._run(cli_runner, results, "--json")
        payload = json.loads(result.output)
        assert payload["ok"] is False
        assert [c["status"] for c in payload["checks"]] == ["pass", "fail"]
        assert payload["checks"][0]["data"] == {"hostname": "[ip]", "wifi_password": "[redacted]"}
        assert result.exit_code == 1

    def test_no_redact_keeps_ips_but_not_secrets(self, cli_runner: CliRunner) -> None:
        results = [CheckResult("config", Status.PASS, "host 10.1.2.3", {"hostname": "10.1.2.3", "token": "t"})]
        result, _ = self._run(cli_runner, results, "--json", "--no-redact")
        data = json.loads(result.output)["checks"][0]["data"]
        assert data == {"hostname": "10.1.2.3", "token": "[redacted]"}

    def test_human_output_masks_ips_by_default(self, cli_runner: CliRunner) -> None:
        result, _ = self._run(cli_runner, [CheckResult("config", Status.PASS, "host 10.1.2.3")])
        assert "10.1.2.3" not in result.output

    def test_options_forwarded(self, cli_runner: CliRunner) -> None:
        _, run_checks = self._run(cli_runner, [], "--no-docker", "--log-lines", "7")
        run_checks.assert_called_once_with(docker=False, log_lines=7)

    def test_log_tail_printed_and_redacted(self, cli_runner: CliRunner) -> None:
        results = [CheckResult("backend logs", Status.PASS, "last 2 lines", {"log_tail": "a password=x 10.0.0.9"})]
        result, _ = self._run(cli_runner, results)
        assert "password=x" not in result.output and "10.0.0.9" not in result.output


@pytest.mark.unit
@pytest.mark.cli
class TestRunChecks:
    def test_invalid_config_skips_backend(self) -> None:
        with (
            patch(
                "th_cli.commands.doctor.check_config", return_value=(CheckResult("config", Status.FAIL, "bad"), None)
            ),
            patch("th_cli.commands.doctor.check_backend") as check_backend,
        ):
            results = doctor_module.run_checks(docker=False, log_lines=0)
        check_backend.assert_not_called()
        assert [r.status for r in results] == [Status.FAIL, Status.SKIP]

    def test_docker_section_is_optional(self) -> None:
        ok = (CheckResult("config", Status.PASS, "ok"), Config())
        with (
            patch("th_cli.commands.doctor.check_config", return_value=ok),
            patch("th_cli.commands.doctor.check_backend", return_value=[]),
            patch("th_cli.commands.doctor.check_docker", return_value=[CheckResult("docker", Status.SKIP, "x")]) as d,
        ):
            assert len(doctor_module.run_checks(docker=True, log_lines=3)) == 2
            d.assert_called_once_with(3)
            assert len(doctor_module.run_checks(docker=False, log_lines=3)) == 1


@pytest.mark.unit
@pytest.mark.cli
class TestDoctorInvocationDetection:
    """A bad config.json normally exits at import; `doctor` must be allowed to report it instead."""

    @pytest.mark.parametrize(
        "argv, expected",
        [
            (["th-cli", "doctor"], True),
            (["th-cli", "doctor", "--json"], True),
            (["th-cli", "--version", "doctor"], True),
            (["th-cli", "project", "list"], False),
            (["th-cli", "project", "doctor"], False),
            (["th-cli"], False),
        ],
    )
    def test_is_doctor_invocation(self, argv: list[str], expected: bool) -> None:
        from th_cli import config as config_module

        with patch.object(config_module.sys, "argv", argv):
            assert config_module._is_doctor_invocation() is expected
