import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEBUG_OUTPUT_PATH = Path(__file__).parent.parent / "debug_llm_output.txt"
_REQUIRED_TOP_LEVEL_KEYS = ("ingredients", "steps")


def parse_llm_recipe_json(raw: str, context: str) -> dict:
    """Save and parse raw LLM JSON, raising clear errors for malformed output."""
    _DEBUG_OUTPUT_PATH.write_text(raw, encoding="utf-8")
    logger.info("Saved raw LLM output for %s to %s", context, _DEBUG_OUTPUT_PATH)
    logger.debug("Raw LLM output for %s: %s", context, raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Malformed JSON from %s: %s", context, exc)
        raise ValueError(
            f"Malformed JSON from LLM during {context}: {exc}. "
            f"Raw output saved to {_DEBUG_OUTPUT_PATH}"
        ) from exc

    missing = [key for key in _REQUIRED_TOP_LEVEL_KEYS if key not in data]
    if missing:
        logger.error("Missing required top-level keys from %s: %s", context, ", ".join(missing))
        raise ValueError(
            f"LLM JSON during {context} is missing required top-level keys: {', '.join(missing)}. "
            f"Raw output saved to {_DEBUG_OUTPUT_PATH}"
        )

    return data
