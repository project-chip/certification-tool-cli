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
"""`th-cli doctor`: diagnose why the CLI cannot talk to the backend."""

import contextlib
import io
import json as jsonlib
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable

import click
import httpx

from th_cli.api_lib_autogen.api_client import SyncApis
from th_cli.api_lib_autogen.exceptions import ResponseHandlingException, UnexpectedResponse, describe_error
from th_cli.client import get_client
from th_cli.colorize import (
    colorize_cmd_help,
    colorize_error,
    colorize_header,
    colorize_help,
    colorize_success,
    colorize_warning,
)
from th_cli.config import Config, get_config_search_paths, load_config
from th_cli.exceptions import ConfigurationError
from th_cli.th_utils.redaction import redact_data, redact_text
from th_cli.utils import get_cli_sha, get_cli_version

PROBE_TIMEOUT_SECONDS = 5.0
DOCKER_TIMEOUT_SECONDS = 10
DOCKER_CONTAINERS = (
    "certification-tool-backend-1",
    "certification-tool-frontend-1",
    "certification-tool-db-1",
    "certification-tool-proxy-1",
)
BACKEND_CONTAINER = DOCKER_CONTAINERS[0]


class Status(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    name: str
    status: Status
    detail: str
    data: dict[str, Any] | None = None


def classify_error(e: Exception) -> str:
    """Say what kind of failure a request error was (refused, DNS, timeout, HTTP status)."""
    if isinstance(e, UnexpectedResponse):
        return f"HTTP {e.status_code} from the backend"

    inner = e.error if isinstance(e, ResponseHandlingException) else e
    chain: list[BaseException] = []
    current: BaseException | None = inner
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__

    if any(isinstance(x, socket.gaierror) for x in chain):
        return f"DNS lookup failed ({describe_error(inner)})"
    if any(isinstance(x, ConnectionRefusedError) for x in chain):
        return "connection refused"
    if isinstance(inner, httpx.TimeoutException):
        return f"timeout ({describe_error(inner)})"
    if isinstance(inner, httpx.ConnectError):
        return f"cannot connect ({describe_error(inner)})"
    return describe_error(e)


def _config_source() -> str:
    paths = get_config_search_paths()
    for path in paths:
        if (path / "config.json").exists():
            return str(path / "config.json")
    for path in paths:
        if (path / "config.json.example").exists():
            return f"{path / 'config.json.example'} (no config.json found)"
    return "built-in defaults (no config.json found)"


def check_config() -> tuple[CheckResult, Config | None]:
    """Load the config the way the CLI does, reporting problems instead of exiting."""
    source = _config_source()
    captured = io.StringIO()
    try:
        # load_config() prints warnings on fallback; capture them so --json stays valid.
        with contextlib.redirect_stdout(captured):
            config = load_config()
    except ConfigurationError as e:
        return CheckResult("config", Status.FAIL, e.message, {"source": source}), None

    warnings = [line.strip() for line in captured.getvalue().splitlines() if line.strip()]
    data = {"source": source, "hostname": config.hostname}
    detail = f"{source}; backend host: {config.hostname}"
    if warnings or "no config.json found" in source:
        return CheckResult("config", Status.WARN, "; ".join([detail, *warnings]), data), config
    return CheckResult("config", Status.PASS, detail, data), config


def _probe(name: str, fn: Callable[[], Any], failure: Status) -> tuple[CheckResult | None, Any]:
    """Run an API call; return (failure result, None) or (None, response)."""
    try:
        return None, fn()
    except (ResponseHandlingException, UnexpectedResponse) as e:
        return CheckResult(name, failure, classify_error(e)), None
    except Exception as e:  # noqa: BLE001 - a diagnostic must report, not crash
        return CheckResult(name, failure, describe_error(e)), None


def check_backend() -> list[CheckResult]:
    """Reachability, version and a few cheap deeper probes."""
    try:
        client = get_client(timeout=httpx.Timeout(PROBE_TIMEOUT_SECONDS))
    except ConfigurationError as e:
        return [CheckResult("backend reachable", Status.FAIL, e.message)]

    try:
        apis = SyncApis(client)
        failure, version = _probe(
            "backend reachable",
            apis.version_api.get_test_harness_backend_version_api_v1_version_get,
            Status.FAIL,
        )
        if failure:
            return [
                failure,
                CheckResult("versions", Status.SKIP, "backend not reachable"),
                CheckResult("test runner", Status.SKIP, "backend not reachable"),
                CheckResult("database", Status.SKIP, "backend not reachable"),
            ]

        backend = version.model_dump(mode="json")
        results = [
            CheckResult("backend reachable", Status.PASS, "GET /api/v1/version answered"),
            CheckResult(
                "versions",
                Status.PASS,
                f"CLI {get_cli_version()} ({get_cli_sha()[:8]}); backend {backend['version']} "
                f"({backend['sha'][:8]}), SDK {backend['sdk_docker_tag']}, db revision {backend['db_revision']}",
                {"cli": {"version": get_cli_version(), "sha": get_cli_sha()}, "backend": backend},
            ),
        ]

        failure, status = _probe(
            "test runner",
            apis.test_run_executions_api.get_test_runner_status_api_v1_test_run_executions_status_get,
            Status.WARN,
        )
        if failure:
            results.append(failure)
        else:
            state = getattr(status.state, "value", status.state)
            results.append(CheckResult("test runner", Status.PASS, f"state: {state}", {"state": str(state)}))

        # A DB-backed endpoint: /version touches no database, so this tells them apart.
        failure, projects = _probe("database", apis.projects_api.read_projects_api_v1_projects__get, Status.WARN)
        results.append(
            failure or CheckResult("database", Status.PASS, f"/projects/ answered ({len(projects)} projects)")
        )
        return results
    finally:
        client.close()


def _run_docker(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", *args],
        capture_output=True,
        text=True,
        timeout=DOCKER_TIMEOUT_SECONDS,
        check=False,
    )


def check_docker(log_lines: int) -> list[CheckResult]:
    """State of the TH containers; skipped cleanly when docker is unavailable."""
    if shutil.which("docker") is None:
        return [CheckResult("docker", Status.SKIP, "docker not found on this host")]

    results = []
    for container in DOCKER_CONTAINERS:
        try:
            proc = _run_docker(["inspect", "-f", "{{.State.Status}}", container])
        except (OSError, subprocess.SubprocessError) as e:
            return [CheckResult("docker", Status.SKIP, f"docker not usable: {describe_error(e)}")]
        state = proc.stdout.strip()
        if proc.returncode != 0:
            results.append(CheckResult(container, Status.WARN, "container not found"))
        elif state == "running":
            results.append(CheckResult(container, Status.PASS, "running"))
        else:
            results.append(CheckResult(container, Status.FAIL, state or "unknown state"))

    if log_lines > 0:
        try:
            proc = _run_docker(["logs", "--tail", str(log_lines), BACKEND_CONTAINER])
            output = (proc.stdout + proc.stderr).strip()
            results.append(CheckResult("backend logs", Status.PASS, f"last {log_lines} lines", {"log_tail": output}))
        except (OSError, subprocess.SubprocessError) as e:
            results.append(CheckResult("backend logs", Status.WARN, describe_error(e)))
    return results


def run_checks(docker: bool, log_lines: int) -> list[CheckResult]:
    config_result, config = check_config()
    results = [config_result]
    if config is None:
        results += [CheckResult("backend reachable", Status.SKIP, "configuration is invalid")]
    else:
        results += check_backend()
    if docker:
        results += check_docker(log_lines)
    return results


_STATUS_LABEL = {
    Status.PASS: (" OK ", colorize_success),
    Status.WARN: ("WARN", colorize_warning),
    Status.FAIL: ("FAIL", colorize_error),
    Status.SKIP: ("SKIP", lambda s: s),
}


def _print_report(results: list[CheckResult], mask_network: bool) -> None:
    click.echo("")
    click.echo(colorize_header("Test Harness CLI Doctor"))
    for result in results:
        label, paint = _STATUS_LABEL[result.status]
        detail = redact_text(result.detail, mask_network)
        click.echo(f"[{paint(label)}] {result.name}: {detail}")
        log_tail = (result.data or {}).get("log_tail")
        if log_tail:
            click.echo(redact_text(log_tail, mask_network))
    failed = [r for r in results if r.status == Status.FAIL]
    click.echo("")
    if failed:
        click.echo(colorize_error(f"{len(failed)} check(s) failed"))
    else:
        click.echo(colorize_success("No problems found"))


@click.command(
    short_help=colorize_help("Diagnose problems reaching the backend"),
    help=colorize_cmd_help(
        "doctor",
        "Check the CLI configuration, backend reachability and versions, and (if available) the "
        "Docker containers. Exits non-zero if a check fails. Secrets, IPs and MACs are masked "
        "unless --no-redact is given.",
    ),
)
@click.option("--json", "as_json", is_flag=True, default=False, help=colorize_help("Print results as JSON"))
@click.option(
    "--no-docker",
    is_flag=True,
    default=False,
    help=colorize_help("Skip the Docker container checks"),
)
@click.option(
    "--log-lines",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help=colorize_help("Include the last N lines of the backend container log (redacted)"),
)
@click.option(
    "--no-redact",
    is_flag=True,
    default=False,
    help=colorize_help("Do not mask IP/MAC addresses (secrets by key name and in logs are always masked)"),
)
@click.pass_context
def doctor(ctx: click.Context, as_json: bool, no_docker: bool, log_lines: int, no_redact: bool) -> None:
    results = run_checks(docker=not no_docker, log_lines=log_lines)
    mask_network = not no_redact

    if as_json:
        payload = {
            "ok": all(r.status != Status.FAIL for r in results),
            "checks": [{**asdict(r), "status": r.status.value} for r in results],
        }
        click.echo(jsonlib.dumps(redact_data(payload, mask_network), indent=2))
    else:
        _print_report(results, mask_network)

    if any(r.status == Status.FAIL for r in results):
        ctx.exit(1)
