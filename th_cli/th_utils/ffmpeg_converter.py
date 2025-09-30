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
import subprocess
import threading
from pathlib import Path
from typing import Optional

import click
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
            stream = (
                ffmpeg.input("pipe:0", format="h264")
                .output("pipe:1", format="mp4", vcodec="copy", movflags="frag_keyframe+empty_moov")
                .overwrite_output()
            )

            self.ffmpeg_process = ffmpeg.run_async(stream, pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)

            # Start thread to read FFmpeg output
            threading.Thread(target=self._read_ffmpeg_output, daemon=True).start()

            logger.info("FFmpeg converter started successfully")
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
                data = self.ffmpeg_process.stdout.read(CHUNK_SIZE)
                if data:
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


class VideoFileConverter:
    """Handles conversion of video files using FFmpeg."""

    @staticmethod
    def convert_video_to_mp4(bin_file_path: Path) -> Optional[Path]:
        """Convert .bin video file to .mp4 using ffmpeg if available."""
        try:
            # Create MP4 filename
            mp4_file = bin_file_path.with_suffix(".mp4")
            click.echo(f"🔄 Converting {bin_file_path.name} to MP4...")

            # Create FFmpeg stream using ffmpeg-python
            stream = (
                ffmpeg.input(str(bin_file_path), format="h264")
                .output(
                    str(mp4_file),
                    vcodec="libx264",
                    preset="fast",
                    crf=23,
                    pix_fmt="yuv420p",
                    movflags="+faststart",
                    r=30,
                )
                .overwrite_output()
            )

            click.echo(f"🎬 Running FFmpeg conversion...")
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, timeout=60)

            if mp4_file.exists():
                file_size = mp4_file.stat().st_size
                click.echo(f"✅ Video converted to MP4: {mp4_file} ({file_size:,} bytes)")

                # Try alternative conversion if first attempt creates very small file
                if file_size < 1024:  # Less than 1KB suggests problem
                    click.echo("⚠️  Small output file, trying alternative conversion...")
                    return VideoFileConverter._try_alternative_conversion(bin_file_path, mp4_file)

                return mp4_file
            else:
                click.echo("❌ FFmpeg conversion failed: Output file not created")
                return VideoFileConverter._try_alternative_conversion(bin_file_path, mp4_file)

        except ffmpeg.Error as e:
            click.echo(f"❌ FFmpeg conversion error: {e}")
            # Try alternative conversion method
            return VideoFileConverter._try_alternative_conversion(bin_file_path, mp4_file)
        except Exception as e:
            click.echo(f"❌ Video conversion error: {e}")
            return None

    @staticmethod
    def _try_alternative_conversion(bin_file_path: Path, mp4_file: Path) -> Optional[Path]:
        """Try alternative FFmpeg conversion methods."""
        alternative_methods = [
            {
                "name": "Raw H.264 with container fix",
                "stream": (
                    ffmpeg.input(str(bin_file_path), format="h264")
                    .output(str(mp4_file), vcodec="copy", bsf="h264_mp4toannexb")
                    .overwrite_output()
                ),
            },
            {
                "name": "Force framerate and format",
                "stream": (
                    ffmpeg.input(str(bin_file_path), format="h264", r=25)
                    .output(str(mp4_file), vcodec="libx264", r=25, pix_fmt="yuv420p")
                    .overwrite_output()
                ),
            },
            {
                "name": "Raw video with size assumption",
                "stream": (
                    ffmpeg.input(str(bin_file_path), format="rawvideo", pix_fmt="yuv420p", s="640x480", r=30)
                    .output(str(mp4_file), vcodec="libx264")
                    .overwrite_output()
                ),
            },
        ]

        for method in alternative_methods:
            try:
                click.echo(f"🔄 Trying: {method['name']}")
                ffmpeg.run(method["stream"], capture_stdout=True, capture_stderr=True, timeout=30)

                if mp4_file.exists() and mp4_file.stat().st_size > 1024:
                    file_size = mp4_file.stat().st_size
                    click.echo(f"✅ Success with {method['name']}: {mp4_file} ({file_size:,} bytes)")
                    return mp4_file

            except Exception as e:
                click.echo(f"   Failed: {e}")
                continue

        click.echo("❌ All conversion methods failed")
        click.echo(f"💡 FFmpeg-python library is installed - check video file format")
        return None
