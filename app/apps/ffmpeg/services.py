import asyncio
import json
import logging
import os
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import ufiles
from fastapi_mongo_base.utils import aionetwork
from fastapi_mongo_base.utils.texttools import sanitize_filename
from server.config import Settings

from .models import Burn

moviepy_process_semaphore = asyncio.Semaphore(1)
promptly_process_semaphore = asyncio.Semaphore(8)


async def get_video_metadata_async(url):
    try:
        # Run ffprobe asynchronously
        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Capture the output and errors
        stdout, stderr = await process.communicate()

        if stderr:
            print(f"Error: {stderr.decode().strip()}")
            return None

        # Parse the JSON output
        metadata = json.loads(stdout.decode())
        duration = (
            float(metadata["format"]["duration"])
            if "format" in metadata and "duration" in metadata["format"]
            else None
        )
        video_stream = next(
            (
                stream
                for stream in metadata.get("streams", [])
                if stream.get("width") and stream.get("height")
            ),
            None,
        )

        width = video_stream["width"] if video_stream else None
        height = video_stream["height"] if video_stream else None

        return {"duration": duration, "width": width, "height": height}
    except Exception as e:
        print(f"Error: {e}")
        return None


async def upload_video(
    file_content: BytesIO,
    file_name: str,
    user_id: uuid.UUID,
    file_upload_dir: str = "subtitles",
    meta_data: dict = {},
):
    ufiles_client = ufiles.AsyncUFiles(
        ufiles_base_url=Settings.UFILES_BASE_URL,
        usso_base_url=Settings.USSO_BASE_URL,
        api_key=Settings.UFILES_API_KEY,
    )
    ufile_item = await ufiles_client.upload_bytes(
        file_content,
        filename=f"{file_upload_dir}/{file_name}",
        public_permission=json.dumps({"permission": ufiles.PermissionEnum.READ}),
        user_id=str(user_id),
        meta_data=meta_data,
    )
    return ufile_item.url


def srt_to_subtitles(subs, video_size):
    import moviepy

    subtitle_clips = []

    for sub in subs:
        start_time = sub.start.to_time()
        end_time = sub.end.to_time()
        start_seconds = (
            start_time.hour * 3600
            + start_time.minute * 60
            + start_time.second
            + start_time.microsecond / 1e6
        )
        end_seconds = (
            end_time.hour * 3600
            + end_time.minute * 60
            + end_time.second
            + end_time.microsecond / 1e6
        )
        duration = end_seconds - start_seconds

        # Formatting text to handle newlines properly
        formatted_text = sub.text.strip()

        # Create a text clip with a black background and white text
        font_path = "./assets/Vazirmatn-Regular.ttf"

        text_bound_clip = (
            moviepy.TextClip(
                text=formatted_text,
                font=font_path,
                font_size=24,
                color="white",
                bg_color="black",
                margin=(4, 4),
                method="caption",
                text_align="center",
                size=(video_size[0] - 20, None),
            )
            .with_opacity(0.75)
            .with_start(start_seconds)
            .with_duration(duration)
            .with_position(
                # ("center", video_size[0] - 50)
                # ("center", "bottom"),
                ("center", 0.8),
                relative=True,
            )
        )
        text_clip = (
            moviepy.TextClip(
                text=formatted_text,
                font=font_path,
                font_size=24,
                color="white",
                margin=(4, 4),
                method="caption",
                text_align="center",
                size=(video_size[0] - 20, None),
            )
            .with_start(start_seconds)
            .with_duration(duration)
            .with_position(
                # ("center", video_size[0] - 50)
                # ("center", "bottom"),
                ("center", 0.8),
                relative=True,
            )
        )

        # Add the text clip to the list of subtitle clips
        subtitle_clips.append(text_bound_clip)
        subtitle_clips.append(text_clip)
    return subtitle_clips


def srt_to_moviepy_subtitles(srt_text: str, video_path: Path, output_path: Path):
    import moviepy
    import pysrt

    video = moviepy.VideoFileClip(video_path)
    subs = pysrt.from_string(srt_text)
    subtitle_clips = srt_to_subtitles(subs, video.size)

    final_video = moviepy.CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(
        output_path,
        fps=video.fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile_path="tmp/",
    )

    # Clean up
    video.close()
    final_video.close()


def get_file_extension(url: str) -> str:
    """
    Extract the file extension from a URL.
    """
    path = urlparse(url).path
    suffix = Path(path).suffix
    if not suffix:
        return ".mp4"
    return suffix


async def burn_subtitles(subtitle_task: Burn):
    from concurrent.futures import ProcessPoolExecutor

    # download video
    video_bytes = await aionetwork.aio_request_binary(url=subtitle_task.url)
    video_path = Path("tmp") / "".join(
        [
            sanitize_filename(subtitle_task.url),
            get_file_extension(subtitle_task.url),
        ]
    )
    with open(video_path, "wb") as f:
        f.write(video_bytes.read())
    output_path = Path("tmp") / f"{sanitize_filename(subtitle_task.url)}_subtitled.mp4"

    async with moviepy_process_semaphore:
        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                srt_to_moviepy_subtitles,
                subtitle_task.translated_srt,
                video_path,
                output_path,
            )

    with open(output_path, "rb") as f:
        video_bytes = BytesIO(f.read())

    uploaded_url = await upload_video(
        video_bytes, output_path.name, subtitle_task.user_id, "subtitles"
    )
    subtitle_task.subtitled_url = uploaded_url
    logging.info(uploaded_url)

    await subtitle_task.save_report("Subtitles burned successfully", emit=False)

    os.remove(video_path)
    os.remove(output_path)
