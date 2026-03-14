import json
import logging
from pathlib import Path

from backend.config import settings
from backend.dependencies import get_openai_client
from backend.models.recipe import Recipe

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "entity_extraction.txt"


async def parse_recipe_text(text: str, source_url: str = "") -> Recipe:
    """Convert raw recipe text into a structured Recipe via GPT."""
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    client = get_openai_client()

    logger.info("Parsing recipe text (%d chars)", len(text))
    response = await client.chat.completions.create(
        model=settings.openai_model_chat,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        max_tokens=4096,
        temperature=0.2,
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    if source_url:
        data["source_url"] = source_url

    recipe = Recipe.model_validate(data)
    logger.info("Parsed recipe: %s (%d steps)", recipe.title, len(recipe.steps))
    return recipe
