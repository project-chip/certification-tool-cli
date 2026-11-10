<!--
 *
 * Copyright (c) 2026 Project CHIP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
-->

# Instructions

Please refer to the main repository for how to use these tools [here](https://github.com/project-chip/certification-tool)


# CSA Certification Tool - CLI

CLI tool for using the CSA Test Harness

## Requirements

1. Ubuntu Server OS
2. Python >= 3.12
3. Poetry installed (see: https://python-poetry.org/docs/#installation)

## Setup

1. Open terminal in the root folder and run the command `./scripts/th_cli_install.sh`
2. Change the url in config.json if required:

```json
    "hostname" : "192.168.x.x" //Change this to your Raspberry Pi IP address/localhost for local development
```

3. Run `th-cli --help` to check available commands

## Commands

```
Commands:
  abort-testing               Abort the current test execution
  available-tests             Get a list of available tests
  project                     Manage the application projects
  rescan-tests                Rescan available test collections
  run-tests                   Create a new test run from selected tests
  test-run-execution          List test run executions and read logs
  test-runner-status          Get the current Matter test runner status
```

### available-tests

Run `th-cli available-tests` to get a list of tests available in Test Harness, printed in YAML. For JSON respond, use `th-cli available-tests --json` .

Options:
- `--json`: Print the JSON response for more details.
- `--compact`: Show test IDs only, 4 per line.
- `--cluster <name>`: Filter by cluster name (e.g. `--cluster ACE`, `CADMIN`, `CC`).
- `--group-by-cluster`: Group test cases by cluster, 4 per line.

### test-runner-status

Run `th-cli test-runner-status` to get the current state of the Matter test runner. For JSON respond, add `--json`.

### abort-testing

Run `th-cli abort-testing` to abort the test run execution that is currently running.

### rescan-tests

Run `th-cli rescan-tests` to make the Test Harness pick up newly added or edited side-loaded test scripts without
restarting the backend. The backend re-discovers all test collections and the command reports what changed, grouped by
test collection:

```
Rescanned test collections successfully (6 found)

Custom SDK Python Tests
  + TC-FAKE-1.1-custom           added
  ~ TC-ACE-1.3-custom            modified
  - TC-OLD-1.1-custom            removed
No changes in: SDK Python Tests, SDK YAML Tests
```

When nothing changed, the command says `No changes detected.`. Scripts that could not be parsed are skipped and listed
with the reason, and the Python files added, modified or removed in the *custom* folder are listed under `Custom files`.

The rescan cannot run while a test is executing: the command fails with `Test Engine is busy.`, so wait for the run to
finish or abort it with `th-cli abort-testing`. See the Side Loading section of the Matter TH User Guide for details.

### run-tests

Run `th-cli run-tests --tests-list <tests> [--title, -n <title>] [--config, -c <config>] [--pics-config-folder, -p <pics-config-folder>] [--tc-params-file, -m <mapping-file>] [--project-id <ID>] [--no-color] [--no-streaming] [--prompt-timeout <seconds>] [-- <extra-sdk-args>]` to start a new test execution.

Required:
- `--tests-list`: Comma-separated list of test case identifiers (e.g. --tests-list TC-ACE-1.1,TC_ACE_1_3)

Optional:
- `--title`: Custom title for the test run. If not provided, the current timestamp will be used as the default.
- `--config`: Path to the JSON config file. **Accepts two formats:**
  - **Config-only**: `{"network": {...}, "dut_config": {...}}`
  - **Full project format**: `{"name": "...", "config": {...}}` (automatically extracts config)
  
  This allows the same JSON file to work with `project create`, `project update`, and `run-tests` commands. If not provided, the project's default configuration will be used.
- `--pics-config-folder`: Path to the folder that contains PICS files. If not specified, no PICS file will be used.
- `--tc-params-file`, `-m`: Path to a JSON file that maps TC IDs to their `test_parameters` (e.g. `int-arg`, `string-arg`, `timeout`). TC IDs are matched case-insensitively with the separators `-`, `_` and `.` normalised, and TC IDs not found in the file are silently skipped. Precedence, lowest to highest: project config, `--tc-params-file`, `--config` file, `--` inline args. See the *TC Parameters Mapping File* section of the Matter TH User Guide.
- `--project-id`: Project ID that this test run belongs to. If not provided, uses the default 'CLI Project Execution' in TH.
- `--no-color`: Disable all colors from the CLI's output text of this test run execution
- `--no-streaming`: Disable the real-time log streaming via web browser (enabled by default).
- `--prompt-timeout`: Override the user-prompt response timeout, in seconds, for this run only (`th_config.prompt_timeout_seconds`).
- `-- <extra-sdk-args>`: Pass additional arguments directly to the SDK container Python tests. Use the double dash (`--`) separator followed by any SDK test arguments. These arguments will be added to every Python test execution in the run.

**Example config files:**

Config-only format:
```json
{
  "network": {
    "wifi": {"ssid": "MyNetwork", "password": "MyPassword"}
  },
  "dut_config": {
    "pairing_mode": "ble-wifi",
    "setup_code": "20202021"
  }
}
```

Full project format (works with all commands):
```json
{
  "name": "My Project",
  "config": {
    "network": {
      "wifi": {"ssid": "MyNetwork", "password": "MyPassword"}
    },
    "dut_config": {
      "pairing_mode": "ble-wifi",
      "setup_code": "20202021"
    }
  }
}
```

**Passing Extra Arguments to SDK Tests:**

You can pass additional arguments directly to the SDK container test execution using the `--` separator. Everything after `--` will be passed as-is to the Python test runner.

Examples:
```bash
# Enable trace logging for all tests in the run
th-cli run-tests -t TC-ACE-1.1 -- --trace-to json:log

# Pass boolean argument
th-cli run-tests -t TC-ACE-1.1,TC-ACE-1.2 -- --bool-arg flag:true

# Pass multiple extra arguments
th-cli run-tests -t TC-ACE-1.1 -- --timeout 60 --int-arg some-arg:1 --bool-arg flag:true

# Combine with other CLI options
th-cli run-tests -t TC-ACE-1.1 --config my-config.json --no-color -- --trace-to json:log
```

Common SDK test arguments you might want to use for example:
- `--endpoint <value>` - Choose the device endpoint
- `--trace-to json:log` - Enable detailed trace logging
- `--timeout <seconds>` - Override default test timeout
- `--int-arg <name>:<value>` - Pass integer argument to test
- `--bool-arg <name>:<true|false>` - Pass boolean argument to test
- `--string-arg <name>:<value>` - Pass string argument to test
- `--hex-arg <name>:<hex-value>` - Pass hex value argument to test

**Note:** These extra arguments are applied to ALL Test Cases in the test run. Invalid arguments could cause test failures, so ensure the arguments are valid for the SDK test framework.

### Test Run Execution

Run `th-cli test-run-execution` (or `th-cli test-run-execution list`) to fetch the history of test runs. Use `--skip` and `--limit` for pagination, `--sort asc|desc` to order by ID (default `desc`), `--project-id` to filter by project, `--archived` to list only archived test runs, and `--all` to fetch every test run with screen pagination (cannot be combined with `--limit`).

Run `th-cli test-run-execution --id {id}` with a test run execution id to fetch the information for that test run.

For JSON respond, add `--json` to the command.

The following subcommands are available: `list`, `log`, `pics-export`, `delete`, `rename`, `archive`, `unarchive`, `repeat`, `export` and `import`.

### Test Run Execution Log

Run `th-cli test-run-execution log --id {id}` to download the log of a test run execution. Use `--output-file` to override the default filename (the test run execution title) and `--grouped` to download a zip archive of the logs grouped by test case state.

The `--log` flag of `th-cli test-run-execution` is deprecated; use this command instead.

### Test Run Execution PICS Export

Run `th-cli test-run-execution pics-export --id {id}` to export the PICS actually used by a test run execution to a zip file. Use `--output-file` to override the default filename (the test run execution title).

### Test Run Execution Delete

Run `th-cli test-run-execution delete --id {id}` to delete a test run execution. It asks for confirmation unless `--yes` is given.

### Test Run Execution Rename

Run `th-cli test-run-execution rename --id {id} --name {new name}` to rename a test run execution. Both parameters are required.

### Test Run Execution Archive and Unarchive

Run `th-cli test-run-execution archive --id {id}` to archive a test run execution, and `th-cli test-run-execution unarchive --id {id}` to restore it. Archived test runs are only listed with `th-cli test-run-execution list --archived`.

### Test Run Execution Repeat

Run `th-cli test-run-execution repeat --id {id}` to create a new test run execution with
the same selected tests and config as an existing one, then start it and attach to it the
same way `run-tests` does (and the frontend's "Repeat" action does): streaming live test
progress and forwarding any user prompts to this terminal. Use `--title` to override the
generated title (defaults to the original title with an updated timestamp; the backend
always appends a timestamp regardless). As with `run-tests`, `--no-color` disables colored
output and `--no-streaming` disables the real-time web log viewer (enabled by default) for
the new execution.

### Test Run Execution Export

Run `th-cli test-run-execution export --id {id}` to export a test run execution's config
and results to a JSON file. Use `--output-file` to override the default filename
(`<execution-title>-execution.json`).

### Test Run Execution Import

Run `th-cli test-run-execution import --file {file} --project-id {id}` to import a test
run execution previously written by `test-run-execution export` into the given project.
The backend rejects the import if the file's `db_revision` doesn't match the destination
instance's current database revision.

### Project Create

Run `th-cli project create --name {project name} --config {config file}` to create a new project. Project name is required. Use `--pics-config-folder` to load the PICS XML files of a directory into the project.

### Project List

Run `th-cli project list` to fetch projects. Use `--skip` and `--limit` for pagination. Use `--archived` to fetch archived projects only.

Run `th-cli project list --id {id}` with a project id to fetch the information for that specific project.

For JSON respond, add `--json` to the command.

### Project Delete

Run `th-cli project delete --id {id}` to delete a project.

### Project Udpdate

Run `th-cli project update --id {id} --config {config file}` to update a project. Both parameters are required. Config must be a full test environment config file.

### Project Edit

Run `th-cli project edit --id {id}` to interactively edit a project's config in your
local editor ($VISUAL/$EDITOR). Only the `config` portion is editable. On save, the
CLI checks for new/unknown keys not present in the original config (the backend does
not reject all unknown fields) and asks for confirmation before persisting. If the
JSON is invalid or the server rejects the change, the editor reopens with your last
edit preserved so nothing is lost.

The editor used is picked from the `$VISUAL` environment variable first, then `$EDITOR`,
falling back to `vim`/`nano`/`vi` if neither is set. To use a different editor, set one
of these before running the command, e.g. `EDITOR=nano th-cli project edit --id {id}`.

### Project Export

Run `th-cli project export --id {id}` to export a project's config to a JSON file. Use `--output-file` to override the default filename (`<project-name>-project-config.json`).

### Project Import

Run `th-cli project import --file {file}` to create a project from a JSON file previously written by `project export`.

### Project Logs

Run `th-cli project logs --id {id}` to download all logs of a project as a single zip archive. Use `--grouped` to download the logs organized by test case state instead of flat log files, and `--output-file` to override the default filename (`<project-name>-logs.zip`).

## Command Colors
By default, the CLI application presents colored texts for all the available commands, specially for the log of test run executions from the `th-cli run-tests` command.
If the users need to disable the colors from the tool's output, they may use one of the options presented below:

1. Use the option flag `--no-color` from the `run-tests` command to remove color for that execution (e.g `th-cli run-tests --no-color -t TC-ACE-1.1`)
2. Prepend the environment variable `TH_CLI_NO_COLOR` set to True to the `run-test` command (e.g `TH_CLI_NO_COLOR=1 th-cli run-tests -t TC-ACE-1.1`)
3. Export the environment variable and use the CLI normally on the same terminal instance (e.g Use `export TH_CLI_NO_COLOR=1` before using the CLI commands)

For the item `3` above, it's possible to change permanently adding the `TH_CLI_NO_COLOR=1` variable to the shell profile (e.g. `~/.bashrc`).
After that, resetting that terminal or any new one will present no color for all the CLI commands.

## Development

The source files are organized in `./th_cli/`.

### Add new command

The project uses [click](https://click.palletsprojects.com/) to declare commands.
To add a new `command` to the CLI:

-   Add a new file in `./th_cli/commands`
-   Import the new command in `./th_cli/commands/__init__.py`
-   Import and add the new command to the `root` group in `./th_cli/main.py`

### VS Code Environment

This project comes with a pre-configured dev-container for VS Code. This takes care of all dependencies and configuring
type-checker, linters and auto-formatting.

### Test Harness API Client

A major component of the CLI is the calling the Test Harness API. We're auto-generating a python client for this API
using [fastapi_client](https://github.com/dmontagu/fastapi_client) based on the `openapi.json` published by the
Test Harness backend.

To update our client:

-   update `openapi.json` in the root of this project
-   run `./scripts/generate_client` (This requires Docker to be installed)

### New Dependencies

The project dependencies are managed with [Poetry](https://python-poetry.org).
To add a new dependency, run `poetry add <package-name>`.

#### Checking Dependencies

The project dependencies may be scanned to look for known vulnerabilities or conflicts for all the poetry packages
configured. For that, run the following command after the tool installation to verify the current status of the
required dependencies:

-  `poetry run python ./scripts/check_deps.py`

### Linting and formatting

The GitHub Project will run linting with Black, Flake8 and mypy on PRs. But these are also available
in convenient scripts:

-   `./scripts/lint.sh`
-   `./scripts/format.sh`

The VS Code dev-container is also configured to do this automatically on file save.
