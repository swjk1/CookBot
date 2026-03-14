"""Basic unit tests for recipe store."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from backend.models.recipe import Recipe, Ingredient, Step


@pytest.fixture
def tmp_recipe_dir(tmp_path):
    """Patch settings to use a temp directory."""
    with patch("backend.services.recipe_store.settings") as mock_settings:
        mock_settings.recipes_path = tmp_path
        yield tmp_path


def make_recipe(**kwargs) -> Recipe:
    defaults = dict(
        title="Test Pasta",
        ingredients=[Ingredient(name="pasta", quantity="200", unit="g")],
        steps=[Step(index=0, instruction="Boil water", duration_seconds=300)],
    )
    defaults.update(kwargs)
    return Recipe(**defaults)


def test_save_and_get_recipe(tmp_recipe_dir):
    from backend.services.recipe_store import save_recipe, get_recipe
    recipe = make_recipe()
    saved = save_recipe(recipe)
    assert saved.id == recipe.id

    loaded = get_recipe(recipe.id)
    assert loaded is not None
    assert loaded.title == "Test Pasta"
    assert len(loaded.steps) == 1


def test_get_missing_recipe(tmp_recipe_dir):
    from backend.services.recipe_store import get_recipe
    assert get_recipe("nonexistent-id") is None


def test_list_recipes(tmp_recipe_dir):
    from backend.services.recipe_store import save_recipe, list_recipes
    r1 = save_recipe(make_recipe(title="Recipe A"))
    r2 = save_recipe(make_recipe(title="Recipe B"))

    summaries = list_recipes()
    titles = [s["title"] for s in summaries]
    assert "Recipe A" in titles
    assert "Recipe B" in titles


def test_delete_recipe(tmp_recipe_dir):
    from backend.services.recipe_store import save_recipe, delete_recipe, get_recipe
    recipe = save_recipe(make_recipe())
    assert delete_recipe(recipe.id) is True
    assert get_recipe(recipe.id) is None
    assert delete_recipe(recipe.id) is False


def test_timer_extraction():
    from backend.services.timer_service import extract_duration_seconds
    assert extract_duration_seconds("Bake for 30 minutes") == 1800
    assert extract_duration_seconds("Cook for 1 hour 15 minutes") == 4500
    assert extract_duration_seconds("Rest for 45 seconds") == 45
    assert extract_duration_seconds("Stir well") is None
