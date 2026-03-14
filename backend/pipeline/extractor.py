import logging
from pathlib import Path

from backend.config import settings
from backend.utils.ffmpeg_utils import extract_audio, extract_keyframes, get_duration

logger = logging.getLogger(__name__)


async def extract_media(video_path: Path, task_id: str) -> tuple[Path, list[Path]]:
    """
    Extract audio and keyframes from a video.
    Returns (audio_path, list_of_keyframe_paths).
    """
    task_dir = settings.media_path / task_id
    audio_dir = task_dir / "audio"
    frames_dir = task_dir / "keyframes"
    audio_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    duration = await get_duration(video_path)
    logger.info("Video duration: %.1f seconds", duration)

    if duration > settings.max_video_duration_seconds:
        raise ValueError(f"Video too long: {duration:.0f}s > {settings.max_video_duration_seconds}s limit")

    audio_path = audio_dir / "audio.mp3"
    audio_path = await extract_audio(video_path, audio_path)

    # 0.5 fps = one frame every 2 seconds
    keyframes = await extract_keyframes(video_path, frames_dir, fps=0.5)

    return audio_path, keyframes
