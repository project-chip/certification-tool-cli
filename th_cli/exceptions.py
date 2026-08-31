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
"""Custom exceptions and error handling for the CLI."""

from typing import Any

import click

from th_cli.api_lib_autogen.exceptions import UnexpectedResponse
from th_cli.colorize import colorize_error


class CLIError(click.ClickException):
    """Base exception for CLI errors."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code

    def show(self, file=None):
        """Show the error message."""
        error_message = colorize_error(f"Error: {self.format_message()}")
        click.echo(error_message, err=True, file=file)


class APIError(CLIError):
    """Exception for API-related errors."""

    def __init__(self, message: str, status_code: int | None = None, content: str | None = None):
        self.status_code = status_code
        self.content = content
        super().__init__(message)

    def format_message(self) -> str:
        """Format the error message with additional context."""
        msg = self.message
        if self.status_code:
            msg += f" (Status: {self.status_code})"
        if self.content:
            msg += f" - {self.content}"
        return msg


class ConfigurationError(CLIError):
    """Exception for configuration-related errors."""

    pass


def _format_api_error_content(content: Any) -> Any:
    """Turn a decoded API error response body into a human-readable string.

    FastAPI error responses are JSON objects, typically {"detail": "..."}
    for a plain error or {"detail": [{"loc": [...], "msg": "...", ...}, ...]}
    for request validation errors. Each list entry is rendered as
    "<field path>: <message>" (e.g. "config.th_config.timeout: value is not
    a valid integer") so which field failed isn't lost when there are
    multiple errors. Falls back to the raw content unchanged for anything
    else (e.g. plain text bodies).
    """
    if not isinstance(content, dict):
        return content

    detail = content.get("detail", content)
    if isinstance(detail, list):
        lines = []
        for error in detail:
            if not isinstance(error, dict):
                lines.append(str(error))
                continue
            # "body" is FastAPI's marker for the request body root; drop it
            # so paths read as e.g. "config.th_config.timeout" rather than
            # "body.config.th_config.timeout".
            loc = ".".join(str(part) for part in error.get("loc", []) if part != "body")
            msg = error.get("msg", "")
            lines.append(f"{loc}: {msg}" if loc else msg)
        return "; ".join(lines) if lines else str(detail)
    return detail


def handle_api_error(e: UnexpectedResponse, operation: str) -> None:
    """Convert API errors to CLI errors."""
    content = e.content
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")
    content = _format_api_error_content(content)
    raise APIError(f"Failed to {operation}", status_code=e.status_code, content=content)


def handle_file_error(e: FileNotFoundError, file_type: str = "file") -> None:
    """Handle file not found errors."""
    raise CLIError(f"{file_type.title()} not found: {e.filename} {e.strerror}")
