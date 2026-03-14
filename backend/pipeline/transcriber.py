import logging
from pathlib import Path

from backend.config import settings
from backend.dependencies import get_openai_client

logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 24 * 1024 * 1024  # 24 MB (Whisper limit is 25 MB)


async def transcribe_audio(audio_path: Path) -> str:
    """Transcribe audio file using OpenAI Whisper. Returns transcript text."""
    client = get_openai_client()
    file_size = audio_path.stat().st_size
    logger.info("Transcribing %s (%.1f MB)", audio_path.name, file_size / 1e6)

    if file_size <= MAX_FILE_BYTES:
        with open(audio_path, "rb") as f:
            response = await client.audio.transcriptions.create(
                model=settings.whisper_model,
                file=f,
                response_format="text",
            )
        return response if isinstance(response, str) else response.text

    # File too large — split into chunks using ffmpeg segment
    logger.warning("Audio file too large (%.1f MB), chunking...", file_size / 1e6)
    return await _transcribe_chunked(audio_path, client)


async def _transcribe_chunked(audio_path: Path, client) -> str:
    """Split audio into 20-minute chunks with 30s overlap and transcribe each."""
    from backend.utils.ffmpeg_utils import run_ffmpeg

    chunk_dir = audio_path.parent / "chunks"
    chunk_dir.mkdir(exist_ok=True)
    chunk_pattern = str(chunk_dir / "chunk_%03d.mp3")

    # 20 min chunks
    await run_ffmpeg(
        "-i", str(audio_path),
        "-f", "segment",
        "-segment_time", "1200",
        "-c", "copy",
        chunk_pattern,
    )

    chunks = sorted(chunk_dir.glob("chunk_*.mp3"))
    transcripts = []
    for chunk in chunks:
        with open(chunk, "rb") as f:
            response = await client.audio.transcriptions.create(
                model=settings.whisper_model,
                file=f,
                response_format="text",
            )
        transcripts.append(response if isinstance(response, str) else response.text)

    return " ".join(transcripts)
