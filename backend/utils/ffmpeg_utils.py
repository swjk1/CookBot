import asyncio
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def run_ffmpeg(*args: str, check: bool = True) -> tuple[int, str, str]:
    """Run ffmpeg with given arguments. Returns (returncode, stdout, stderr)."""
    cmd = ["ffmpeg", "-y", *args]
    logger.debug("ffmpeg cmd: %s", " ".join(cmd))

    def _run():
        return subprocess.run(cmd, capture_output=True)

    result = await asyncio.to_thread(_run)
    rc = result.returncode
    stdout = result.stdout.decode(errors="replace")
    stderr = result.stderr.decode(errors="replace")
    if check and rc != 0:
        raise RuntimeError(f"ffmpeg failed (rc={rc}): {stderr[-2000:]}")
    return rc, stdout, stderr


async def extract_audio(video_path: Path, output_path: Path) -> Path:
    """Extract mono 64 kbps mp3 from video."""
    await run_ffmpeg(
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-b:a", "64k",
        str(output_path),
    )
    return output_path


async def extract_keyframes(video_path: Path, output_dir: Path, fps: float = 0.5) -> list[Path]:
    """Extract keyframes at `fps` frames-per-second into output_dir as JPEGs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(output_dir / "frame_%04d.jpg")
    await run_ffmpeg(
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-q:v", "2",
        pattern,
    )
    frames = sorted(output_dir.glob("frame_*.jpg"))
    logger.info("Extracted %d keyframes from %s", len(frames), video_path.name)
    return frames


async def get_duration(video_path: Path) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]

    def _run():
        return subprocess.run(cmd, capture_output=True)

    result = await asyncio.to_thread(_run)
    try:
        return float(result.stdout.decode().strip())
    except ValueError:
        return 0.0
