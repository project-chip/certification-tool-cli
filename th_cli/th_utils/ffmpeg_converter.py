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
import queue
import threading
from typing import Optional

import ffmpeg
from loguru import logger

# Constants
CHUNK_SIZE = 8192  # 8KB chunks for optimal streaming performance


class FFmpegStreamConverter:
    """Converts H.264 raw stream to MP4 in real-time using FFmpeg."""

    def __init__(self):
        self.ffmpeg_process = None
        self.output_queue = queue.Queue()

    def start_conversion(self):
        """Start FFmpeg process for real-time conversion."""
        try:
            # Create FFmpeg stream using ffmpeg-python
            # Re-encode to browser-compatible H.264 baseline profile for live streaming
            stream = (
                ffmpeg.input("pipe:0", format="h264")
                .output(
                    "pipe:1",
                    format="mp4",
                    vcodec="libx264",
                    preset="ultrafast",  # Fast encoding for real-time
                    tune="zerolatency",  # Minimize latency
                    profile="baseline",  # Most compatible H.264 profile
                    level="3.0",  # Compatible level
                    pix_fmt="yuv420p",  # Browser-compatible pixel format
                    movflags="frag_keyframe+empty_moov+default_base_moof",  # Optimized for streaming
                    **{"g": 30, "keyint_min": 30},  # Keyframe every 30 frames for seeking
                )
                .overwrite_output()
            )

            self.ffmpeg_process = ffmpeg.run_async(stream, pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)

            # Start thread to read FFmpeg output
            threading.Thread(target=self._read_ffmpeg_output, daemon=True).start()

            logger.info("FFmpeg converter started successfully with browser-compatible H.264 baseline profile")
            return True

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg not available or failed to start: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to start FFmpeg converter: {e}")
            return False

    def _read_ffmpeg_output(self):
        """Read converted MP4 data from FFmpeg stdout."""
        try:
            while self.ffmpeg_process and self.ffmpeg_process.poll() is None:
                if data := self.ffmpeg_process.stdout.read(CHUNK_SIZE):
                    try:
                        self.output_queue.put_nowait(data)
                    except queue.Full:
                        pass  # Drop frames if queue is full
        except Exception as e:
            logger.error(f"Error reading FFmpeg output: {e}")

    def feed_data(self, h264_data: bytes):
        """Feed H.264 raw data to FFmpeg for conversion."""
        if self.ffmpeg_process and self.ffmpeg_process.stdin:
            try:
                self.ffmpeg_process.stdin.write(h264_data)
                self.ffmpeg_process.stdin.flush()
            except Exception as e:
                logger.error(f"Error feeding data to FFmpeg: {e}")

    def get_converted_data(self, timeout=1.0):
        """Get converted MP4 data."""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        """Stop FFmpeg conversion."""
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping FFmpeg: {e}")
            finally:
                self.ffmpeg_process = None
