"""Custom exceptions and error handling for the CLI."""

from typing import Optional

import click

from app.api_lib_autogen.exceptions import UnexpectedResponse


class CLIError(click.ClickException):
    """Base exception for CLI errors."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code

    def show(self, file=None):
        """Show the error message."""
        click.echo(f"Error: {self.format_message()}", err=True, file=file)


class APIError(CLIError):
    """Exception for API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, content: Optional[str] = None):
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


def handle_api_error(e: UnexpectedResponse, operation: str) -> None:
    """Convert API errors to CLI errors."""
    raise APIError(f"Failed to {operation}", status_code=e.status_code, content=e.content)


def handle_file_error(e: FileNotFoundError, file_type: str = "file") -> None:
    """Handle file not found errors."""
    raise CLIError(f"{file_type.title()} not found: {e.filename} {e.strerror}")
