import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _has_text_overlay(image_path: Path) -> bool:
    """Quick check: does image have high-contrast text-like regions?"""
    try:
        from PIL import Image, ImageFilter
        import numpy as np

        img = Image.open(image_path).convert("L")
        edges = img.filter(ImageFilter.FIND_EDGES)
        arr = np.array(edges)
        # High edge density suggests text overlay
        return float(arr.mean()) > 8.0
    except Exception:
        return True  # If unsure, run OCR anyway


async def ocr_frame(image_path: Path) -> Optional[str]:
    """Run PaddleOCR on a single frame. Returns extracted text or None."""
    if not _has_text_overlay(image_path):
        return None

    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        result = ocr.ocr(str(image_path), cls=True)
        if not result or not result[0]:
            return None
        lines = [line[1][0] for line in result[0] if line[1][1] > 0.6]
        text = " | ".join(lines)
        logger.debug("OCR on %s: %s", image_path.name, text[:100])
        return text if text else None
    except ImportError:
        logger.warning("PaddleOCR not installed, skipping OCR")
        return None
    except Exception as exc:
        logger.warning("OCR failed on %s: %s", image_path.name, exc)
        return None


async def ocr_frames(frame_paths: list[Path]) -> list[tuple[int, str]]:
    """Run OCR on all frames, return list of (frame_index, text) for frames with text."""
    results = []
    for i, path in enumerate(frame_paths):
        text = await ocr_frame(path)
        if text:
            results.append((i, text))
    logger.info("OCR: %d/%d frames had text overlays", len(results), len(frame_paths))
    return results
