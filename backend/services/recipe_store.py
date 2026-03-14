import logging
import orjson
from typing import Optional

from backend.db.database import get_pool
from backend.models.recipe import Recipe

logger = logging.getLogger(__name__)


async def save_recipe(recipe: Recipe) -> Recipe:
    pool = get_pool()
    data = orjson.dumps(recipe.model_dump(mode="json")).decode()
    await pool.execute(
        """
        INSERT INTO recipes (id, title, created_at, data)
        VALUES ($1, $2, $3, $4::jsonb)
        ON CONFLICT (id) DO UPDATE
            SET title = EXCLUDED.title,
                data  = EXCLUDED.data
        """,
        recipe.id, recipe.title, recipe.created_at, data,
    )
    logger.info("Saved recipe %s (%s)", recipe.id, recipe.title)
    return recipe


async def get_recipe(recipe_id: str) -> Optional[Recipe]:
    pool = get_pool()
    row = await pool.fetchrow("SELECT data FROM recipes WHERE id = $1", recipe_id)
    if not row:
        return None
    return Recipe.model_validate(orjson.loads(row["data"]))


async def list_recipes() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch("SELECT data FROM recipes ORDER BY created_at DESC")
    summaries = []
    for row in rows:
        try:
            recipe = Recipe.model_validate(orjson.loads(row["data"]))
            summaries.append(recipe.summary())
        except Exception as exc:
            logger.warning("Skipping malformed recipe: %s", exc)
    return summaries


async def delete_recipe(recipe_id: str) -> bool:
    pool = get_pool()
    result = await pool.execute("DELETE FROM recipes WHERE id = $1", recipe_id)
    deleted = result.split()[-1] != "0"
    if deleted:
        logger.info("Deleted recipe %s", recipe_id)
    return deleted
