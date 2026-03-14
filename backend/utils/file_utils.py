from pathlib import Path
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


def create_storage_dirs() -> None:
    dirs = [
        settings.recipes_path,
        settings.sessions_path,
        settings.downloads_path,
        settings.audio_cache_path,
        settings.keyframes_path,
        settings.thumbnails_path,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Storage directories ready at %s", settings.storage_base)


def safe_filename(name: str, max_len: int = 200) -> str:
    """Sanitize a string for use as a filename."""
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    return "".join(c if c in keep else "_" for c in name)[:max_len]
