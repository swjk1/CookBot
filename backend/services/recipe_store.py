import orjson
import logging
from pathlib import Path
from typing import Optional

from backend.config import settings
from backend.models.recipe import Recipe

logger = logging.getLogger(__name__)


def _recipe_path(recipe_id: str) -> Path:
    return settings.recipes_path / f"{recipe_id}.json"


def save_recipe(recipe: Recipe) -> Recipe:
    path = _recipe_path(recipe.id)
    path.write_bytes(orjson.dumps(recipe.model_dump(mode="json"), option=orjson.OPT_INDENT_2))
    logger.info("Saved recipe %s (%s)", recipe.id, recipe.title)
    return recipe


def get_recipe(recipe_id: str) -> Optional[Recipe]:
    path = _recipe_path(recipe_id)
    if not path.exists():
        return None
    data = orjson.loads(path.read_bytes())
    return Recipe.model_validate(data)


def list_recipes() -> list[dict]:
    summaries = []
    for p in sorted(settings.recipes_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = orjson.loads(p.read_bytes())
            recipe = Recipe.model_validate(data)
            summaries.append(recipe.summary())
        except Exception as exc:
            logger.warning("Skipping malformed recipe %s: %s", p.name, exc)
    return summaries


def delete_recipe(recipe_id: str) -> bool:
    path = _recipe_path(recipe_id)
    if not path.exists():
        return False
    path.unlink()
    logger.info("Deleted recipe %s", recipe_id)
    return True
