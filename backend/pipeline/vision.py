import base64
import logging
from pathlib import Path

from backend.config import settings
from backend.dependencies import get_openai_client

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "vision_caption.txt"
MAX_FRAMES_PER_BATCH = 20  # stay within token limits


def _encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


async def caption_frame(image_path: Path) -> str:
    """Caption a single keyframe using GPT-4o vision."""
    prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    b64 = _encode_image(image_path)
    client = get_openai_client()

    response = await client.chat.completions.create(
        model=settings.openai_model_vision,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}},
                ],
            }
        ],
        max_tokens=200,
    )
    return response.choices[0].message.content or ""


async def caption_frames(frame_paths: list[Path], sample_rate: int = 4) -> list[tuple[int, str]]:
    """
    Caption a sampled subset of frames.
    sample_rate=4 means every 4th frame (since we extract at 0.5fps = one per 2s, this is every 8s).
    Returns list of (frame_index, caption).
    """
    import asyncio

    sampled = [(i, p) for i, p in enumerate(frame_paths) if i % sample_rate == 0]
    sampled = sampled[:MAX_FRAMES_PER_BATCH]  # cap

    logger.info("Captioning %d frames with GPT-4o vision", len(sampled))

    async def _cap(idx: int, path: Path) -> tuple[int, str]:
        try:
            caption = await caption_frame(path)
            return idx, caption
        except Exception as exc:
            logger.warning("Vision caption failed for frame %d: %s", idx, exc)
            return idx, ""

    results = await asyncio.gather(*[_cap(i, p) for i, p in sampled])
    return [(i, c) for i, c in results if c]
