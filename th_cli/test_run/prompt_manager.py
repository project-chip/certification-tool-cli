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
import asyncio
import json
import os
import queue
import re
import socket
import time
from typing import Any, Union

import aioconsole
import click
import httpx
from websockets.client import WebSocketClientProtocol

from th_cli.colorize import colorize_error, colorize_key_value, italic
from th_cli.config import config
from th_cli.shared_constants import MessageKeysEnum, MessageTypeEnum

from .camera.camera_http_server import CameraHTTPServer
from .camera.image_handler import ImageVerificationHandler
from .camera.two_way_talk_handler import TwoWayTalkHandler
from .socket_schemas import (
    ImageVerificationPromptRequest,
    MessagePromptRequest,
    OptionsSelectPromptRequest,
    PromptRequest,
    PromptResponse,
    PushAVStreamVerificationRequest,
    StreamVerificationPromptRequest,
    TextInputPromptRequest,
    TwoWayTalkVerificationRequest,
    UserResponseStatusEnum,
)

# Constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
UPLOAD_TIMEOUT_SECONDS = 300.0
CONNECT_TIMEOUT_SECONDS = 10.0

# Global video handler instance for reuse
_video_handler_instance = None


def _get_local_ip() -> str:
    """Get the local IP address of the machine."""
    try:
        # Connect to a remote address to determine local IP
        # This doesn't actually send data, just determines routing
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        # Fallback to localhost if unable to determine IP
        return "localhost"


async def handle_prompt(
    socket: WebSocketClientProtocol,
    request: PromptRequest,
    message_type: str = None,
    two_way_talk_handler=None,
) -> None:
    """Handle all types of prompts with correct inheritance order."""
    click.echo("=======================================")

    if message_type == MessageTypeEnum.IMAGE_VERIFICATION_REQUEST or isinstance(
        request, ImageVerificationPromptRequest
    ):
        await _handle_image_verification_prompt(socket=socket, prompt=request)
    elif message_type == MessageTypeEnum.TWO_WAY_TALK_VERIFICATION_REQUEST or isinstance(
        request, TwoWayTalkVerificationRequest
    ):
        await _handle_two_way_talk_prompt(socket=socket, prompt=request, handler=two_way_talk_handler)
    elif message_type == MessageTypeEnum.STREAM_VERIFICATION_REQUEST or isinstance(
        request, StreamVerificationPromptRequest
    ):
        await __handle_stream_verification_prompt(socket=socket, prompt=request)
    elif message_type == MessageTypeEnum.PUSH_AV_STREAM_VERIFICATION_REQUEST or isinstance(
        request, PushAVStreamVerificationRequest
    ):
        await _handle_push_av_stream_prompt(socket=socket, prompt=request)
    elif message_type == MessageTypeEnum.MESSAGE_REQUEST or isinstance(request, MessagePromptRequest):
        await __handle_message_prompt(socket=socket, prompt=request)
    elif isinstance(request, OptionsSelectPromptRequest):
        await __handle_options_prompt(socket=socket, prompt=request)
    elif isinstance(request, TextInputPromptRequest):
        await __handle_text_prompt(socket=socket, prompt=request)
    else:
        click.echo(colorize_error(f"Unsupported prompt request: {request.__class__.__name__}"))

    click.echo("=======================================")


def _get_video_handler():
    """Get or create a reusable video handler instance."""
    global _video_handler_instance
    if _video_handler_instance is None:
        # Import here to avoid circular import
        from .camera import CameraStreamHandler

        _video_handler_instance = CameraStreamHandler()
    return _video_handler_instance


async def _cleanup_video_handler():
    """Clean up the global video handler instance."""
    global _video_handler_instance
    if _video_handler_instance is not None:
        try:
            await _video_handler_instance.stop_video_capture_and_stream()
        except Exception:
            pass  # Ignore cleanup errors


async def __handle_stream_verification_prompt(socket: WebSocketClientProtocol, prompt: PromptRequest) -> None:
    """Handle video stream verification prompts."""
    try:
        # Validate prompt has required attributes
        if not hasattr(prompt, "options") or not prompt.options:
            click.echo(colorize_error("Video prompt missing required options"), err=True)
            return

        # Get reusable video handler instance
        video_handler = _get_video_handler()
        video_handler.set_prompt_data(prompt.prompt, prompt.options)

        # Start capturing with streaming
        _ = await video_handler.start_video_capture_and_stream(str(prompt.message_id))

        # Wait for stream to be ready instead of fixed delay
        stream_ready = await video_handler.wait_for_stream_ready(timeout=10.0)
        if not stream_ready:
            # Display specific error if available
            if video_handler.initialization_error:
                click.echo(video_handler.initialization_error, err=True)
            else:
                click.echo(colorize_error("Video stream failed to initialize"), err=True)

            # Send CANCELLED response to abort test execution
            await _send_prompt_response(
                socket=socket,
                prompt=prompt,
                response="Video stream initialization failed",
                status_code=UserResponseStatusEnum.CANCELLED,
            )
            return

        click.echo(italic(prompt.prompt))
        local_ip = _get_local_ip()
        click.echo(f"🎬 Please verify the video at: http://{local_ip}:{video_handler.http_server.port}")

        click.echo("Waiting for your response in the web interface...")

        # Wait for user response from web UI instead of CLI input
        user_answer = await video_handler.wait_for_user_response(float(prompt.timeout))

        if user_answer is None:
            click.echo(colorize_error("No response received from web interface"), err=True)
            return

        # Display the user's selected response
        selected_option = None
        for option_text, option_id in prompt.options.items():
            if option_id == user_answer:
                selected_option = option_text
                break

        if selected_option:
            click.echo(f"✅ User selected: {colorize_key_value(str(user_answer), selected_option)}")
        else:
            click.echo(f"✅ User response: {user_answer}")

        # Stop video capture and streaming
        _ = await video_handler.stop_video_capture_and_stream()

        await _send_prompt_response(socket=socket, response=user_answer, prompt=prompt)

    except asyncio.exceptions.TimeoutError:
        click.echo(colorize_error("Video prompt timed out"), err=True)
        # Clean up using the shared instance
        await _cleanup_video_handler()
    except Exception as e:
        click.echo(colorize_error(f"Error handling video prompt: {e}"), err=True)
        # Clean up using the shared instance
        await _cleanup_video_handler()


async def _handle_image_verification_prompt(
    socket: WebSocketClientProtocol, prompt: ImageVerificationPromptRequest
) -> None:
    """Handle image verification prompts via HTTP server."""
    try:
        # Convert hex string back to bytes (format: "ff,d8,ff,e0" → bytes)
        image_hex_clean = prompt.image_hex_str.replace(", ", "").replace(",", "")
        image_data = bytes.fromhex(image_hex_clean)

        # Use existing ImageVerificationHandler
        image_handler = ImageVerificationHandler()
        image_handler.set_prompt_data(prompt.prompt, prompt.options, image_data)

        # Start HTTP server
        await image_handler.start_image_server()

        # Show user instructions
        local_ip = _get_local_ip()
        click.echo("📸 Image verification required!")
        click.echo(f"🌐 Open: http://{local_ip}:{image_handler.http_server.port}")
        click.echo(f"📝 {prompt.prompt}")
        click.echo(f"⏰ Timeout: {prompt.timeout}s")

        # Wait for user response
        user_answer = await image_handler.wait_for_user_response(float(prompt.timeout))

        # Clean up
        image_handler.stop_image_server()

        if user_answer is None:
            click.echo(colorize_error("❌ No response received - timed out"), err=True)
            return

        # Display the user's selected response
        selected_option = None
        for option_text, option_id in prompt.options.items():
            if option_id == user_answer:
                selected_option = option_text
                break

        if selected_option:
            click.echo(f"✅ User selected: {colorize_key_value(str(user_answer), selected_option)}")
        else:
            click.echo(f"✅ User response: {user_answer}")

        # Send response back to test
        await _send_prompt_response(socket=socket, response=user_answer, prompt=prompt)

    except Exception as e:
        click.echo(colorize_error(f"❌ Error handling image verification: {e}"), err=True)


async def _handle_two_way_talk_prompt(
    socket: WebSocketClientProtocol, prompt: OptionsSelectPromptRequest, handler=None
) -> None:
    """Handle two-way talk verification via browser page on port 8999."""
    if handler is None:
        # Handler not injected. Do NOT call start_waiting() — it runs fuser -k
        # which would kill this process (which holds port 8999).
        # Create a fresh server on the same port without freeing it first.
        click.echo("WARNING: TwoWayTalk handler not available — creating fallback server", err=True)
        handler = TwoWayTalkHandler(port=8999)
        try:
            handler.start_server_only()
        except OSError as e:
            click.echo(colorize_error(f"Could not start fallback server: {e}"), err=True)

    handler.show_prompt(prompt_text=prompt.prompt, prompt_options=prompt.options)
    local_ip = _get_local_ip()
    try:
        click.echo("🎤 Two-Way Talk Verification")
        click.echo(italic(prompt.prompt))
        click.echo(f"   Open http://{local_ip}:8999 to verify audio/video and select PASS or FAIL.")
        click.echo("   Waiting for your response in the browser...")
        user_answer = await handler.wait_for_user_response(float(prompt.timeout))
        if user_answer is None:
            click.echo(colorize_error("Two-way talk prompt timed out"), err=True)
            return
        selected_option = next((k for k, v in prompt.options.items() if v == user_answer), str(user_answer))
        click.echo(f"✅ User selected: {selected_option}")
        await _send_prompt_response(socket=socket, response=user_answer, prompt=prompt)
    finally:
        handler.stop()


async def _handle_push_av_stream_prompt(
    socket: WebSocketClientProtocol, prompt: PushAVStreamVerificationRequest
) -> None:
    """Handle Push AV Stream verification prompts.

    This displays information about verifying video uploaded to the external Push AV Server,
    and provides a simple web UI for the user to respond with PASS/FAIL.
    """
    try:
        # Validate prompt has required attributes
        if not hasattr(prompt, "options") or not prompt.options:
            click.echo(colorize_error("Push AV Stream prompt missing required options"), err=True)
            return

        # Try to determine Push AV Server URL
        # Default to https://localhost:1234
        local_ip = _get_local_ip()
        push_av_server_url = f"https://{local_ip}:1234"

        http_server = CameraHTTPServer()
        response_queue = queue.Queue()

        # Start HTTP server with Push AV Stream verification page
        # Pass None for video_handler since we're not streaming video
        http_server.start(
            mp4_queue=None,  # No video streaming needed
            response_queue=response_queue,
            video_handler=None,  # No video handler needed
            prompt_options=prompt.options,
            prompt_text=prompt.prompt,
            is_push_av_verification=True,  # Use Push AV template
            push_av_server_url=push_av_server_url,  # Pass Push AV Server URL
            local_ip=local_ip,  # Pass local IP for proxy URL construction
        )

        # Display instructions
        verification_url = f"http://{local_ip}:{http_server.port}"
        click.echo(italic(prompt.prompt))
        click.echo("📡 Push AV Stream Verification")
        click.echo(f"🌐 Please verify at: {verification_url}")
        click.echo("   The web interface will show available streams and allow playback.")
        click.echo("")
        click.echo("Waiting for your response in the web interface...")

        # Wait for user response from web UI
        user_answer = None
        start_time = time.time()
        timeout = float(prompt.timeout)

        while time.time() - start_time < timeout:
            try:
                user_answer = response_queue.get_nowait()
                break
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue

        # Stop HTTP server
        http_server.stop()

        if user_answer is None:
            click.echo(colorize_error("No response received from web interface"), err=True)
            return

        # Display the user's selected response
        selected_option = None
        for option_text, option_id in prompt.options.items():
            if option_id == user_answer:
                selected_option = option_text
                break

        if selected_option:
            click.echo(f"✅ User selected: {colorize_key_value(str(user_answer), selected_option)}")
        else:
            click.echo(f"✅ User response: {user_answer}")

        await _send_prompt_response(socket=socket, response=user_answer, prompt=prompt)

    except Exception as e:
        click.echo(colorize_error(f"Error handling Push AV Stream prompt: {e}"), err=True)


async def handle_file_upload_request(socket: WebSocketClientProtocol, request: PromptRequest) -> None:
    """Handle file upload requests from the backend."""
    click.echo("=======================================")
    await __handle_file_upload_prompt(socket=socket, prompt=request)
    click.echo("=======================================")


async def __handle_options_prompt(socket: WebSocketClientProtocol, prompt: OptionsSelectPromptRequest) -> None:
    try:
        user_answer = await asyncio.wait_for(_prompt_user_for_option(prompt), float(prompt.timeout))
        await _send_prompt_response(socket=socket, response=user_answer, prompt=prompt)
    except asyncio.exceptions.TimeoutError:
        click.echo(colorize_error("Prompt timed out"), err=True)
        pass


async def __handle_message_prompt(socket: WebSocketClientProtocol, prompt: PromptRequest) -> None:
    """Handle simple message prompts that only require acknowledgment."""
    click.echo(italic(prompt.prompt))
    await _send_prompt_response(socket=socket, response="ACK", prompt=prompt)


async def _prompt_user_for_option(prompt: OptionsSelectPromptRequest) -> int:
    # Print Prompt
    click.echo(italic(prompt.prompt))
    for key in prompt.options.keys():
        id = prompt.options[key]
        click.echo(f"  {colorize_key_value(str(id), key)}")
    click.echo(italic("Please enter a number for an option above: "))

    # Wait for input async
    input = await aioconsole.ainput()

    # validate input
    try:
        input_int = int(input)
        if input_int in prompt.options.values():
            return input_int
    except ValueError:
        pass

    # Recursively Retry
    await asyncio.sleep(0.1)
    click.echo(colorize_error(f"Invalid input {input}"), err=True)
    return await _prompt_user_for_option(prompt)


async def __handle_text_prompt(socket: WebSocketClientProtocol, prompt: TextInputPromptRequest) -> None:
    try:
        user_answer = await asyncio.wait_for(__prompt_user_for_text_input(prompt), float(prompt.timeout))
        await _send_prompt_response(socket=socket, response=user_answer, prompt=prompt)
    except asyncio.exceptions.TimeoutError:
        click.echo(colorize_error("Prompt timed out"), err=True)
        pass


async def __handle_file_upload_prompt(socket: WebSocketClientProtocol, prompt: PromptRequest) -> None:
    """Handle the file upload prompt and user interaction."""
    try:
        file_path = await asyncio.wait_for(__prompt_user_for_file_upload(prompt), float(prompt.timeout))
        if file_path:
            await __upload_file_and_send_response(socket=socket, file_path=file_path, prompt=prompt)
        else:
            # User cancelled or provided empty path
            await _send_prompt_response(socket=socket, response="", prompt=prompt)
    except asyncio.exceptions.TimeoutError:
        click.echo("File upload prompt timed out", err=True)
        pass


async def __prompt_user_for_text_input(prompt: TextInputPromptRequest) -> str:
    # Print Prompt
    click.echo(italic(prompt.prompt))

    # Display placeholder text if available
    if prompt.placeholder_text:
        click.echo(f"  Hint: {prompt.placeholder_text}")

    # Display default value if available
    prompt_suffix = ""
    if prompt.default_value is not None:
        prompt_suffix = f" [default: {prompt.default_value}]"

    click.echo(f"Enter value{prompt_suffix}: ", nl=False)

    # Wait for input async
    user_input = await aioconsole.ainput()

    # Use default value if input is empty and default exists
    if not user_input.strip() and prompt.default_value is not None:
        user_input = prompt.default_value
        click.echo(f"Using default value: {user_input}")

    # validate input
    if __valid_text_input(input=user_input, prompt=prompt):
        return user_input

    # Recursively Retry
    await asyncio.sleep(0.1)
    click.echo(colorize_error(f"Invalid input {input}"), err=True)
    return await __prompt_user_for_text_input(prompt)


async def __prompt_user_for_file_upload(prompt: PromptRequest) -> str:
    """Prompt the user to provide a file path for upload."""
    # Print Prompt
    click.echo(prompt.prompt)

    while True:
        click.echo("Enter the path to the file to upload (or press Enter to skip): ")

        # Wait for input async
        file_path = await aioconsole.ainput()

        # If user just pressed Enter, return empty string
        if not file_path.strip():
            return ""

        # Validate file path and type
        if __valid_file_upload(file_path=file_path, prompt=prompt):
            return file_path

        # Show error and retry (avoiding recursion)
        await asyncio.sleep(0.1)
        click.echo(f"Invalid file path or type: {file_path}", err=True)


async def __upload_file_and_send_response(
    socket: WebSocketClientProtocol, file_path: str, prompt: PromptRequest
) -> None:
    """Send file path as response - let backend handle actual upload."""
    try:
        if not os.path.isfile(file_path):
            click.echo(f"Error: File '{file_path}' does not exist or is not accessible", err=True)
            await _send_prompt_response(socket=socket, response="", prompt=prompt)
            return

        file_size = os.path.getsize(file_path)

        # Check file size limit
        if file_size > MAX_FILE_SIZE:
            click.echo(f"❌ File too large: {file_size} bytes (max: {MAX_FILE_SIZE} bytes)", err=True)
            await _send_prompt_response(socket=socket, response="", prompt=prompt)
            return

        click.echo(f"File selected: {file_path} (size: {file_size:,} bytes)")

        # Build upload URL - handle both hostname and hostname:port formats
        base_url = config.hostname
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        upload_url = f"{base_url}/api/v1/test_run_executions/file_upload/"

        # Set timeout for large file uploads
        timeout = httpx.Timeout(UPLOAD_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            with open(file_path, "rb") as file:
                files = {"file": (os.path.basename(file_path), file, "application/octet-stream")}

                response = await client.post(upload_url, files=files)

                response.raise_for_status()
                click.echo("✅ File uploaded successfully")
                await _send_prompt_response(socket=socket, response="SUCCESS", prompt=prompt)

    except httpx.RequestError as e:
        click.echo(f"❌ Network error during file upload: {str(e)}", err=True)
        await _send_prompt_response(socket=socket, response="", prompt=prompt)
    except httpx.HTTPStatusError as e:
        click.echo(f"❌ HTTP error during file upload: {e.response.status_code} - {e.response.text}", err=True)
        await _send_prompt_response(socket=socket, response="", prompt=prompt)
    except Exception as e:
        click.echo(f"❌ Unexpected error uploading file: {str(e)}", err=True)
        await _send_prompt_response(socket=socket, response="", prompt=prompt)


def __valid_text_input(input: Any, prompt: TextInputPromptRequest) -> bool:
    if not isinstance(input, str):
        return False

    if prompt.regex_pattern is None:
        return True

    return re.match(prompt.regex_pattern, input) is not None


def __valid_file_upload(file_path: str, prompt: PromptRequest) -> bool:
    """Validate that the file path is valid and the file is accessible."""

    if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
        return False

    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in [".txt", ".log"]:
        click.echo(f"Error: Invalid file type '{file_ext}'. Only .txt and .log files are supported.", err=True)
        return False

    return True


async def _send_prompt_response(
    socket: WebSocketClientProtocol,
    prompt: PromptRequest,
    response: Union[str, int],
    status_code: UserResponseStatusEnum = UserResponseStatusEnum.OKAY,
) -> None:
    """
    Send a prompt response to the backend.

    Args:
        socket: WebSocket connection to send the response through
        prompt: The original prompt request
        response: The response data (user input, error message, etc.)
        status_code: Status of the response (OKAY, CANCELLED, TIMEOUT, INVALID)
    """
    response_obj = PromptResponse(
        response=response,
        status_code=status_code,
        message_id=prompt.message_id,
    )
    payload_dict = {
        MessageKeysEnum.TYPE: "prompt_response",
        MessageKeysEnum.PAYLOAD: response_obj.model_dump(),
    }
    payload = json.dumps(payload_dict)
    await socket.send(payload)
