import logging
import time
from pathlib import Path

from backend.config import settings
from backend.dependencies import get_openai_client
from backend.models.recipe import Recipe
from backend.utils.llm_json import parse_llm_recipe_json

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "entity_extraction.txt"


async def parse_recipe_text(text: str, source_url: str = "") -> Recipe:
    """Convert raw recipe text into a structured Recipe via GPT."""
    request_start = time.perf_counter()
    print("[timing] request received: parse_recipe_text")

    prompt_start = time.perf_counter()
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    print(f"[timing] prompt load took {time.perf_counter() - prompt_start:.2f}s")
    client = get_openai_client()

    logger.info("Parsing recipe text (%d chars)", len(text))
    parser_start = time.perf_counter()
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
    print(f"[timing] parser call took {time.perf_counter() - parser_start:.2f}s")

    raw = response.choices[0].message.content or "{}"
    data = parse_llm_recipe_json(raw, "text parser")
    if source_url:
        data["source_url"] = source_url

    recipe = Recipe.model_validate(data)
    logger.info("Parsed recipe: %s (%d steps)", recipe.title, len(recipe.steps))
    print(f"[timing] total response time took {time.perf_counter() - request_start:.2f}s")
    return recipe
