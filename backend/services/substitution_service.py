import logging
from backend.config import settings
from backend.dependencies import get_openai_client
from backend.models.recipe import Recipe
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "substitution.txt"


async def get_substitution(recipe: Recipe, ingredient: str, reason: str = "") -> str:
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    recipe_context = f"Recipe: {recipe.title}\nIngredients: {', '.join(i.name for i in recipe.ingredients)}"
    prompt = template.format(
        recipe_context=recipe_context,
        ingredient=ingredient,
        reason=reason or "not specified",
    )

    client = get_openai_client()
    response = await client.chat.completions.create(
        model=settings.openai_model_chat,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4,
    )
    return response.choices[0].message.content or ""
