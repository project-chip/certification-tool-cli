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
import datetime
import queue
import socket
from typing import Optional

from loguru import logger

from .logs_http_server import LogsHTTPServer


class LogStreamHandler:
    """Main coordinator for real-time log streaming functionality."""

    def __init__(self, port: int = 8998):
        """Initialize the log stream handler.
        
        Args:
            port: Port number for the HTTP server (default: 8998)
        """
        self.port = port
        self.http_server = LogsHTTPServer(port=port)
        self.log_queue: queue.Queue = queue.Queue(maxsize=1000)
        self.is_running = False
        self.log_file_path: Optional[str] = None
        
    def start(self, test_run_title: str = "Test Execution", log_file_path: Optional[str] = None) -> str:
        """Start the log streaming HTTP server.
        
        Args:
            test_run_title: Title of the test run for display
            log_file_path: Path to the log file for download functionality
            
        Returns:
            URL where logs can be viewed
        """
        if self.is_running:
            logger.warning("Log stream handler already running")
            return self._get_log_viewer_url()
        
        try:
            # Store log file path for download functionality
            self.log_file_path = log_file_path
            
            # Get local IP address
            local_ip = self._get_local_ip()
            
            # Start HTTP server
            self.http_server.start(
                log_queue=self.log_queue,
                test_run_title=test_run_title,
                local_ip=local_ip,
                log_file_path=log_file_path,
            )
            
            self.is_running = True
            
            viewer_url = f"http://{local_ip}:{self.port}"
            logger.info(f"Log stream viewer started: {viewer_url}")
            
            return viewer_url
            
        except Exception as e:
            logger.error(f"Failed to start log stream handler: {e}")
            raise
    
    def stop(self):
        """Stop the log streaming HTTP server."""
        if not self.is_running:
            return
        
        try:
            # Signal end of stream
            if not self.log_queue.full():
                try:
                    self.log_queue.put_nowait(None)
                except queue.Full:
                    pass
            
            # Stop HTTP server
            self.http_server.stop()
            
            self.is_running = False
            logger.info("Log stream handler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping log stream handler: {e}")
    
    def add_log_entry(
        self,
        message: str,
        level: str = "INFO",
        timestamp: Optional[str] = None
    ):
        """Add a log entry to the stream.
        
        Args:
            message: Log message text
            level: Log level (INFO, WARNING, ERROR, DEBUG, etc.)
            timestamp: ISO format timestamp (auto-generated if not provided)
        """
        if not self.is_running:
            return
        
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        log_entry = {
            "message": message,
            "level": level.upper(),
            "timestamp": timestamp,
        }
        
        try:
            # Try to add to queue without blocking
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            # Queue is full, skip this entry silently to avoid blocking
            # This is acceptable for real-time streaming when no browser is connected
            pass
    
    def _get_local_ip(self) -> str:
        """Get the local IP address of the machine.
        
        Returns:
            Local IP address as string, or 'localhost' if unable to determine
        """
        try:
            # Create a socket connection to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connect to an external host (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "localhost"
    
    def _get_log_viewer_url(self) -> str:
        """Get the URL for the log viewer.
        
        Returns:
            Log viewer URL
        """
        local_ip = self._get_local_ip()
        return f"http://{local_ip}:{self.port}"
